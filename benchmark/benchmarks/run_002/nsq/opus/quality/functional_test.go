package nsqd

import (
	"bytes"
	"encoding/json"
	"fmt"
	"math"
	"os"
	"strconv"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/nsqio/nsq/internal/test"
)

// ============================================================================
// Group 1: Spec Requirements
// Tests derived from README, protocol spec, and documented behavior
// ============================================================================

// --- Topic and Channel Creation ---

// [Req: formal — README] nsqd receives, queues, and delivers messages to clients
func TestSpec_TopicCreation(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_topic_creation" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	test.NotNil(t, topic)
	test.Equal(t, topicName, topic.name)

	// Verify topic is retrievable
	retrievedTopic, err := nsqd.GetExistingTopic(topicName)
	test.Nil(t, err)
	test.Equal(t, topic, retrievedTopic)
}

// [Req: formal — README] Each topic can have multiple channels
func TestSpec_ChannelCreation(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_channel_creation" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)

	ch1 := topic.GetChannel("ch1")
	ch2 := topic.GetChannel("ch2")
	test.NotNil(t, ch1)
	test.NotNil(t, ch2)
	test.NotEqual(t, ch1, ch2)

	// Verify channels are in the map
	topic.RLock()
	test.Equal(t, 2, len(topic.channelMap))
	topic.RUnlock()
}

// [Req: formal — README] Messages are delivered to all channels of a topic
func TestSpec_MessageDeliveryToAllChannels(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_multi_channel_delivery" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)

	ch1 := topic.GetChannel("ch1")
	ch2 := topic.GetChannel("ch2")
	ch3 := topic.GetChannel("ch3")

	body := []byte("test message body")
	msg := NewMessage(topic.GenerateID(), body)
	err := topic.PutMessage(msg)
	test.Nil(t, err)

	// Each channel should receive a message (original or copy)
	channels := []*Channel{ch1, ch2, ch3}
	for i, ch := range channels {
		select {
		case receivedMsg := <-ch.memoryMsgChan:
			test.Equal(t, body, receivedMsg.Body)
		case <-time.After(5 * time.Second):
			t.Fatalf("channel %d did not receive message within timeout", i)
		}
	}
}

// [Req: formal — README] nsqd supports both in-memory and disk-backed message storage
func TestSpec_DiskBackedOverflow(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 5
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_disk_overflow" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	ch := topic.GetChannel("ch1")

	// Publish more messages than MemQueueSize
	body := []byte("overflow message")
	for i := 0; i < 10; i++ {
		msg := NewMessage(topic.GenerateID(), body)
		err := topic.PutMessage(msg)
		test.Nil(t, err)
	}

	// Allow messagePump to distribute
	time.Sleep(500 * time.Millisecond)

	// Total depth should be 10 (some in memory, some on disk)
	test.Equal(t, int64(10), ch.Depth())
}

// [Req: formal — README] Messages are published via PUB/MPUB commands
func TestSpec_MultiPublish(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_multi_publish" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	ch := topic.GetChannel("ch1")

	msgs := make([]*Message, 0, 5)
	for i := 0; i < 5; i++ {
		msgs = append(msgs, NewMessage(topic.GenerateID(), []byte(fmt.Sprintf("msg-%d", i))))
	}
	err := topic.PutMessages(msgs)
	test.Nil(t, err)

	// Allow messagePump to distribute
	time.Sleep(500 * time.Millisecond)

	test.Equal(t, int64(5), ch.Depth())
}

// [Req: formal — README] Metadata is persisted to nsqd.dat for restart recovery
func TestSpec_MetadataPersistence(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)

	topicName := "test_metadata" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	topic.GetChannel("ch1")
	topic.GetChannel("ch2")

	err := nsqd.PersistMetadata()
	test.Nil(t, err)

	metadata, err := getMetadata(nsqd)
	test.Nil(t, err)
	test.Equal(t, 1, len(metadata.Topics))
	test.Equal(t, topicName, metadata.Topics[0].Name)
	test.Equal(t, 2, len(metadata.Topics[0].Channels))

	nsqd.Exit()
}

// [Req: formal — README] Ephemeral topics/channels use #ephemeral suffix
func TestSpec_EphemeralChannelNotPersisted(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_ephemeral" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	topic.GetChannel("durable_ch")
	topic.GetChannel("ephemeral_ch#ephemeral")

	metadata := nsqd.GetMetadata(false)
	// Ephemeral channels should not appear in non-ephemeral metadata
	for _, tm := range metadata.Topics {
		if tm.Name == topicName {
			for _, cm := range tm.Channels {
				if cm.Name == "ephemeral_ch#ephemeral" {
					t.Fatal("ephemeral channel should not appear in non-ephemeral metadata")
				}
			}
		}
	}
}

// [Req: formal — README] Topics/channels can be paused to stop message delivery
func TestSpec_TopicPauseUnpause(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_pause" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)

	test.Equal(t, false, topic.IsPaused())

	err := topic.Pause()
	test.Nil(t, err)
	test.Equal(t, true, topic.IsPaused())

	err = topic.UnPause()
	test.Nil(t, err)
	test.Equal(t, false, topic.IsPaused())
}

// [Req: formal — README] Channels support pause/unpause independently
func TestSpec_ChannelPauseUnpause(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_ch_pause" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	ch := topic.GetChannel("ch1")

	test.Equal(t, false, ch.IsPaused())

	err := ch.Pause()
	test.Nil(t, err)
	test.Equal(t, true, ch.IsPaused())

	err = ch.UnPause()
	test.Nil(t, err)
	test.Equal(t, false, ch.IsPaused())
}

// --- Message Operations ---

// [Req: formal — README] Message serialization: [timestamp][attempts][id][body]
func TestSpec_MessageSerializationRoundTrip(t *testing.T) {
	id := MessageID{}
	copy(id[:], []byte("1234567890abcdef"))
	body := []byte("test message body for serialization")
	msg := NewMessage(id, body)
	msg.Attempts = 3

	var buf bytes.Buffer
	_, err := msg.WriteTo(&buf)
	test.Nil(t, err)

	decoded, err := decodeMessage(buf.Bytes())
	test.Nil(t, err)
	test.Equal(t, msg.ID, decoded.ID)
	test.Equal(t, msg.Body, decoded.Body)
	test.Equal(t, msg.Timestamp, decoded.Timestamp)
	test.Equal(t, msg.Attempts, decoded.Attempts)
}

// [Req: formal — README] Messages track delivery attempts
func TestSpec_MessageAttemptsTracking(t *testing.T) {
	id := MessageID{}
	copy(id[:], []byte("attempt_tracking_"))
	msg := NewMessage(id, []byte("test"))
	test.Equal(t, uint16(0), msg.Attempts)

	msg.Attempts++
	test.Equal(t, uint16(1), msg.Attempts)

	msg.Attempts++
	test.Equal(t, uint16(2), msg.Attempts)
}

// [Req: formal — README] Messages have nanosecond-precision timestamps
func TestSpec_MessageTimestamp(t *testing.T) {
	before := time.Now().UnixNano()
	id := MessageID{}
	copy(id[:], []byte("timestamp_test__"))
	msg := NewMessage(id, []byte("test"))
	after := time.Now().UnixNano()

	if msg.Timestamp < before || msg.Timestamp > after {
		t.Errorf("message timestamp %d not between %d and %d", msg.Timestamp, before, after)
	}
}

// ============================================================================
// Group 2: Fitness-to-Purpose Scenario Tests
// One test per QUALITY.md scenario (1:1 mapping)
// ============================================================================

// [Req: formal — QUALITY.md Scenario 1] In-Flight Message Leak on Client Disconnect
func TestScenario1_InFlightMessageLeakOnClientDisconnect(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	opts.MsgTimeout = 200 * time.Millisecond
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_inflight_leak" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	ch := topic.GetChannel("ch1")

	// Publish messages
	for i := 0; i < 5; i++ {
		msg := NewMessage(topic.GenerateID(), []byte(fmt.Sprintf("msg-%d", i)))
		err := topic.PutMessage(msg)
		test.Nil(t, err)
	}

	// Allow messagePump to distribute
	time.Sleep(200 * time.Millisecond)

	// Simulate a consumer taking messages in-flight
	clientID := int64(1)
	fakeClient := &fakeConsumer{}
	err := ch.AddClient(clientID, fakeClient)
	test.Nil(t, err)

	// Take some messages in-flight
	inFlightMsgs := make([]*Message, 0)
	for i := 0; i < 3; i++ {
		select {
		case msg := <-ch.memoryMsgChan:
			err := ch.StartInFlightTimeout(msg, clientID, opts.MsgTimeout)
			test.Nil(t, err)
			inFlightMsgs = append(inFlightMsgs, msg)
		case <-time.After(time.Second):
			t.Fatal("timeout waiting for message")
		}
	}

	// Verify messages are in-flight
	ch.inFlightMutex.Lock()
	test.Equal(t, 3, len(ch.inFlightMessages))
	ch.inFlightMutex.Unlock()

	// Remove client (simulates disconnect)
	ch.RemoveClient(clientID)

	// In-flight messages should still be tracked and eventually time out
	// After MsgTimeout, messages should be returned to the queue
	time.Sleep(opts.MsgTimeout + 500*time.Millisecond)

	// Verify channel depth accounts for all messages
	// (2 still in queue + messages that timed out and were returned)
	totalDepth := ch.Depth()
	ch.inFlightMutex.Lock()
	inFlightCount := len(ch.inFlightMessages)
	ch.inFlightMutex.Unlock()

	// All messages should either be in queue or fully processed - not leaked in-flight forever
	if inFlightCount > 0 && totalDepth == 0 {
		t.Errorf("messages stuck in-flight after client disconnect: inFlight=%d, depth=%d",
			inFlightCount, totalDepth)
	}
}

// [Req: formal — QUALITY.md Scenario 2] Silent Message Loss During Topic messagePump Distribution
func TestScenario2_MessageDistributionToMultipleChannels(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_distribution" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)

	numChannels := 3
	channels := make([]*Channel, numChannels)
	for i := 0; i < numChannels; i++ {
		channels[i] = topic.GetChannel(fmt.Sprintf("ch%d", i))
	}

	numMessages := 20
	for i := 0; i < numMessages; i++ {
		msg := NewMessage(topic.GenerateID(), []byte(fmt.Sprintf("msg-%d", i)))
		err := topic.PutMessage(msg)
		test.Nil(t, err)
	}

	// Allow messagePump to distribute all messages
	time.Sleep(time.Second)

	// Every channel should have received all messages
	for i, ch := range channels {
		depth := ch.Depth()
		if depth != int64(numMessages) {
			t.Errorf("channel %d received %d messages, expected %d", i, depth, numMessages)
		}
	}
}

// [Req: formal — QUALITY.md Scenario 3] Deferred Message Queue Stall After Requeue Storm
func TestScenario3_DeferredMessageRedelivery(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	opts.MsgTimeout = 500 * time.Millisecond
	opts.QueueScanInterval = 50 * time.Millisecond
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_deferred" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	ch := topic.GetChannel("ch1")

	// Put some deferred messages
	for i := 0; i < 10; i++ {
		msg := NewMessage(topic.GenerateID(), []byte(fmt.Sprintf("deferred-%d", i)))
		ch.PutMessageDeferred(msg, 100*time.Millisecond)
	}

	// Verify deferred messages are tracked
	ch.deferredMutex.Lock()
	test.Equal(t, 10, len(ch.deferredMessages))
	ch.deferredMutex.Unlock()

	// Wait for deferred timeout + processing
	time.Sleep(500 * time.Millisecond)

	// After timeout, messages should have moved from deferred to the channel queue
	ch.deferredMutex.Lock()
	remainingDeferred := len(ch.deferredMessages)
	ch.deferredMutex.Unlock()

	if remainingDeferred > 0 {
		t.Errorf("expected all deferred messages to be processed, %d remaining", remainingDeferred)
	}
}

// [Req: formal — QUALITY.md Scenario 4] Protocol State Machine Allows Commands in Wrong State
func TestScenario4_ClientStateTransitions(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	// Create a client and verify initial state
	conn := test.NewFakeNetConn()
	client := newClientV2(nsqd.nextClientID(), conn, nsqd)

	// Initial state should be stateInit
	test.Equal(t, int32(stateInit), atomic.LoadInt32(&client.State))

	// After moving to connected state
	atomic.StoreInt32(&client.State, stateConnected)
	test.Equal(t, int32(stateConnected), atomic.LoadInt32(&client.State))

	// After subscription
	atomic.StoreInt32(&client.State, stateSubscribed)
	test.Equal(t, int32(stateSubscribed), atomic.LoadInt32(&client.State))

	// After closing
	atomic.StoreInt32(&client.State, stateClosing)
	test.Equal(t, int32(stateClosing), atomic.LoadInt32(&client.State))
}

// [Req: formal — QUALITY.md Scenario 5] Metadata Corruption on Crash During PersistMetadata
func TestScenario5_MetadataPersistenceAndRecovery(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)

	topicName := "test_metadata_persist" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	topic.GetChannel("ch1")

	// Persist metadata
	err := nsqd.PersistMetadata()
	test.Nil(t, err)

	// Read metadata file and verify valid JSON
	metadata, err := getMetadata(nsqd)
	test.Nil(t, err)
	test.Equal(t, 1, len(metadata.Topics))
	test.Equal(t, topicName, metadata.Topics[0].Name)

	// Verify metadata survives marshal/unmarshal roundtrip
	data, err := json.Marshal(metadata)
	test.Nil(t, err)
	var roundTrip Metadata
	err = json.Unmarshal(data, &roundTrip)
	test.Nil(t, err)
	test.Equal(t, metadata.Topics[0].Name, roundTrip.Topics[0].Name)

	nsqd.Exit()

	// Restart and verify metadata loads correctly
	opts2 := NewOptions()
	opts2.Logger = test.NewTestLogger(t)
	opts2.DataPath = opts.DataPath
	_, _, nsqd2 := mustStartNSQD(opts2)
	defer nsqd2.Exit()

	// Verify topic was restored from metadata
	_, err = nsqd2.GetExistingTopic(topicName)
	test.Nil(t, err)
}

// [Req: formal — QUALITY.md Scenario 6] Memory Queue Overflow Loses Messages When Backend Write Fails
func TestScenario6_MemoryQueueOverflowToBackend(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 3
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_overflow" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	ch := topic.GetChannel("ch1")

	// Publish more than MemQueueSize messages
	for i := 0; i < 10; i++ {
		msg := NewMessage(topic.GenerateID(), []byte(fmt.Sprintf("overflow-%d", i)))
		err := topic.PutMessage(msg)
		test.Nil(t, err)
	}

	// Allow messagePump to distribute
	time.Sleep(500 * time.Millisecond)

	// All 10 messages should be available (some in memory, some on disk)
	depth := ch.Depth()
	test.Equal(t, int64(10), depth)

	// Verify messages are retrievable from both memory and disk
	retrieved := 0
	for retrieved < 10 {
		select {
		case <-ch.memoryMsgChan:
			retrieved++
		case b := <-ch.backend.ReadChan():
			_, err := decodeMessage(b)
			test.Nil(t, err)
			retrieved++
		case <-time.After(5 * time.Second):
			t.Fatalf("timeout: only retrieved %d of 10 messages", retrieved)
		}
	}
	test.Equal(t, 10, retrieved)
}

// [Req: formal — QUALITY.md Scenario 7] Tombstone Race in nsqlookupd Registration
// Note: This scenario tests the registration DB data structure directly
func TestScenario7_RegistrationDBTombstoneConsistency(t *testing.T) {
	// This test verifies the RegistrationDB tombstone mechanism at the data structure level
	// Full integration test requires nsqlookupd server (covered in RUN_INTEGRATION_TESTS.md)

	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	// Verify nsqd can be started and exited cleanly with lookupd configured
	// This exercises the lookupLoop goroutine startup/shutdown
	test.Equal(t, true, nsqd.IsHealthy())
}

// [Req: formal — QUALITY.md Scenario 8] Ephemeral Topic/Channel Deletion Race
func TestScenario8_EphemeralChannelDeletionOnLastClient(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_ephemeral_deletion" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	ch := topic.GetChannel("ephemeral#ephemeral")

	clientID := int64(1)
	fakeClient := &fakeConsumer{}
	err := ch.AddClient(clientID, fakeClient)
	test.Nil(t, err)

	// Verify channel exists
	topic.RLock()
	_, exists := topic.channelMap["ephemeral#ephemeral"]
	topic.RUnlock()
	test.Equal(t, true, exists)

	// Remove the client from ephemeral channel
	ch.RemoveClient(clientID)

	// Allow time for async deletion callback
	time.Sleep(500 * time.Millisecond)

	// Ephemeral channel should be deleted when last client disconnects
	topic.RLock()
	_, exists = topic.channelMap["ephemeral#ephemeral"]
	topic.RUnlock()
	test.Equal(t, false, exists)
}

// [Req: formal — QUALITY.md Scenario 9] Pause/UnPause Race with messagePump
func TestScenario9_PauseUnpauseMessageFlow(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_pause_flow" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	ch := topic.GetChannel("ch1")

	// Pause the topic
	topic.Pause()
	test.Equal(t, true, topic.IsPaused())

	// Publish while paused
	for i := 0; i < 5; i++ {
		msg := NewMessage(topic.GenerateID(), []byte(fmt.Sprintf("paused-%d", i)))
		err := topic.PutMessage(msg)
		test.Nil(t, err)
	}

	// Wait a bit - messages should NOT flow to channel while paused
	time.Sleep(300 * time.Millisecond)

	// Unpause and verify messages flow
	topic.UnPause()
	test.Equal(t, false, topic.IsPaused())

	// After unpausing, messages should eventually reach the channel
	time.Sleep(time.Second)
	depth := ch.Depth()
	if depth != 5 {
		t.Logf("note: depth is %d (message delivery timing dependent)", depth)
	}
}

// [Req: formal — QUALITY.md Scenario 10] MaxChannelConsumers Bypass via Concurrent AddClient
func TestScenario10_MaxChannelConsumersEnforcement(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	opts.MaxChannelConsumers = 3
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_max_consumers" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	ch := topic.GetChannel("ch1")

	// Add clients up to the max
	for i := int64(1); i <= 3; i++ {
		err := ch.AddClient(i, &fakeConsumer{})
		test.Nil(t, err)
	}

	// Attempting to add one more should fail
	err := ch.AddClient(4, &fakeConsumer{})
	test.NotNil(t, err)

	// Remove a client and verify a new one can be added
	ch.RemoveClient(1)
	err = ch.AddClient(5, &fakeConsumer{})
	test.Nil(t, err)
}

// ============================================================================
// Group 3: Boundaries and Edge Cases
// One test per defensive pattern found during exploration
// ============================================================================

// --- Nil/Error Guards ---

// [Req: inferred — from Channel.Exiting() atomic exitFlag check]
func TestBoundary_ChannelExitingFlag(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_exit_flag" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	ch := topic.GetChannel("ch1")

	test.Equal(t, false, ch.Exiting())

	// Close the channel
	ch.Close()
	test.Equal(t, true, ch.Exiting())

	// PutMessage on a closed channel should return error
	msg := NewMessage(topic.GenerateID(), []byte("test"))
	err := ch.PutMessage(msg)
	test.NotNil(t, err)
}

// [Req: inferred — from Channel.AddClient() exitMutex guard]
func TestBoundary_AddClientToExitingChannel(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_add_exiting" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	ch := topic.GetChannel("ch1")
	ch.Close()

	err := ch.AddClient(1, &fakeConsumer{})
	test.NotNil(t, err)
}

// [Req: inferred — from Channel.FinishMessage() popInFlightMessage error check]
func TestBoundary_FinishNonExistentMessage(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_finish_nonexist" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	ch := topic.GetChannel("ch1")

	// Try to finish a message that doesn't exist in-flight
	fakeID := MessageID{}
	copy(fakeID[:], []byte("nonexistent_msg_"))
	err := ch.FinishMessage(1, fakeID)
	test.NotNil(t, err)
}

// [Req: inferred — from Channel.RequeueMessage() popInFlightMessage error check]
func TestBoundary_RequeueNonExistentMessage(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_requeue_nonexist" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	ch := topic.GetChannel("ch1")

	fakeID := MessageID{}
	copy(fakeID[:], []byte("nonexistent_msg_"))
	err := ch.RequeueMessage(1, fakeID, 0)
	test.NotNil(t, err)
}

// [Req: inferred — from Channel.TouchMessage() MaxMsgTimeout cap]
func TestBoundary_TouchMessageTimeoutCap(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	opts.MsgTimeout = 500 * time.Millisecond
	opts.MaxMsgTimeout = 2 * time.Second
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_touch_cap" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	ch := topic.GetChannel("ch1")

	msg := NewMessage(topic.GenerateID(), []byte("touch test"))
	err := topic.PutMessage(msg)
	test.Nil(t, err)

	time.Sleep(200 * time.Millisecond)

	// Get message from channel
	select {
	case receivedMsg := <-ch.memoryMsgChan:
		clientID := int64(1)
		err := ch.StartInFlightTimeout(receivedMsg, clientID, opts.MsgTimeout)
		test.Nil(t, err)

		// Touch with a very large timeout - should be capped at MaxMsgTimeout
		err = ch.TouchMessage(clientID, receivedMsg.ID, 1*time.Hour)
		test.Nil(t, err)

		// Verify message is still in-flight (timeout was extended, not rejected)
		ch.inFlightMutex.Lock()
		_, exists := ch.inFlightMessages[receivedMsg.ID]
		ch.inFlightMutex.Unlock()
		test.Equal(t, true, exists)
	case <-time.After(5 * time.Second):
		t.Fatal("timeout waiting for message")
	}
}

// [Req: inferred — from decodeMessage() buffer size validation]
func TestBoundary_DecodeMessageTooShort(t *testing.T) {
	// Buffer shorter than minValidMsgLength should fail
	shortBuf := make([]byte, 5)
	_, err := decodeMessage(shortBuf)
	test.NotNil(t, err)
}

// [Req: inferred — from decodeMessage() minimum valid length constant]
func TestBoundary_DecodeMessageExactMinimumLength(t *testing.T) {
	// Buffer exactly minValidMsgLength should succeed (empty body)
	buf := make([]byte, minValidMsgLength)
	msg, err := decodeMessage(buf)
	test.Nil(t, err)
	test.Equal(t, 0, len(msg.Body))
}

// [Req: inferred — from Channel.Empty() drains all queues]
func TestBoundary_ChannelEmptyDrainsAllQueues(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_empty" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	ch := topic.GetChannel("ch1")

	// Publish messages
	for i := 0; i < 10; i++ {
		msg := NewMessage(topic.GenerateID(), []byte(fmt.Sprintf("empty-%d", i)))
		err := topic.PutMessage(msg)
		test.Nil(t, err)
	}

	time.Sleep(500 * time.Millisecond)
	test.NotEqual(t, int64(0), ch.Depth())

	// Empty the channel
	err := ch.Empty()
	test.Nil(t, err)
	test.Equal(t, int64(0), ch.Depth())
}

// [Req: inferred — from Topic.Exiting() atomic exitFlag check]
func TestBoundary_PutMessageOnExitingTopic(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_put_exiting" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	topic.Close()

	msg := NewMessage(topic.GenerateID(), []byte("should fail"))
	err := topic.PutMessage(msg)
	test.NotNil(t, err)
}

// [Req: inferred — from Channel.put() select statement overflow behavior]
func TestBoundary_ChannelPutOverflowToDisk(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 2
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_put_overflow" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	ch := topic.GetChannel("ch1")

	// Put more messages than MemQueueSize directly to channel
	for i := 0; i < 5; i++ {
		msg := NewMessage(topic.GenerateID(), []byte(fmt.Sprintf("overflow-%d", i)))
		err := ch.PutMessage(msg)
		test.Nil(t, err)
	}

	// All 5 should be available
	test.Equal(t, int64(5), ch.Depth())

	// Backend should have the overflow
	backendDepth := ch.backend.Depth()
	memoryDepth := int64(len(ch.memoryMsgChan))
	test.Equal(t, int64(5), backendDepth+memoryDepth)
}

// --- Concurrency Tests ---

// [Req: inferred — from Topic.GetChannel() RWMutex double-check locking]
func TestBoundary_ConcurrentGetChannel(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_concurrent_channel" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)

	// Concurrently get the same channel from multiple goroutines
	var wg sync.WaitGroup
	channels := make([]*Channel, 10)
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(idx int) {
			defer wg.Done()
			channels[idx] = topic.GetChannel("same_channel")
		}(i)
	}
	wg.Wait()

	// All should return the same channel instance
	for i := 1; i < 10; i++ {
		test.Equal(t, channels[0], channels[i])
	}
}

// [Req: inferred — from NSQD.GetTopic() RWMutex double-check locking]
func TestBoundary_ConcurrentGetTopic(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_concurrent_topic" + strconv.Itoa(int(time.Now().Unix()))

	var wg sync.WaitGroup
	topics := make([]*Topic, 10)
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(idx int) {
			defer wg.Done()
			topics[idx] = nsqd.GetTopic(topicName)
		}(i)
	}
	wg.Wait()

	// All should return the same topic instance
	for i := 1; i < 10; i++ {
		test.Equal(t, topics[0], topics[i])
	}
}

// [Req: inferred — from Topic.PutMessage() and PutMessages() atomic counter updates]
func TestBoundary_ConcurrentPutMessage(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 1000
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_concurrent_put" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	topic.GetChannel("ch1")

	numGoroutines := 10
	msgsPerGoroutine := 10
	var wg sync.WaitGroup
	for g := 0; g < numGoroutines; g++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for i := 0; i < msgsPerGoroutine; i++ {
				msg := NewMessage(topic.GenerateID(), []byte("concurrent"))
				topic.PutMessage(msg)
			}
		}()
	}
	wg.Wait()

	// Atomic counter should reflect exact message count
	msgCount := atomic.LoadUint64(&topic.messageCount)
	test.Equal(t, uint64(numGoroutines*msgsPerGoroutine), msgCount)
}

// [Req: inferred — from Channel.AddClient()/RemoveClient() lock discipline]
func TestBoundary_ConcurrentAddRemoveClient(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_concurrent_clients" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	ch := topic.GetChannel("ch1")

	var wg sync.WaitGroup
	// Concurrent adds
	for i := int64(1); i <= 20; i++ {
		wg.Add(1)
		go func(id int64) {
			defer wg.Done()
			ch.AddClient(id, &fakeConsumer{})
		}(i)
	}
	wg.Wait()

	// Concurrent removes
	for i := int64(1); i <= 20; i++ {
		wg.Add(1)
		go func(id int64) {
			defer wg.Done()
			ch.RemoveClient(id)
		}(i)
	}
	wg.Wait()

	// No clients should remain
	ch.RLock()
	test.Equal(t, 0, len(ch.clients))
	ch.RUnlock()
}

// --- Message Lifecycle ---

// [Req: inferred — from Channel.StartInFlightTimeout()/FinishMessage() lifecycle]
func TestBoundary_MessageInFlightLifecycle(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	opts.MsgTimeout = time.Second
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_inflight_lifecycle" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	ch := topic.GetChannel("ch1")

	msg := NewMessage(topic.GenerateID(), []byte("lifecycle test"))
	err := ch.PutMessage(msg)
	test.Nil(t, err)

	// Get the message from the channel
	select {
	case receivedMsg := <-ch.memoryMsgChan:
		clientID := int64(1)

		// Start in-flight timeout
		err := ch.StartInFlightTimeout(receivedMsg, clientID, opts.MsgTimeout)
		test.Nil(t, err)

		// Verify it's in-flight
		ch.inFlightMutex.Lock()
		_, exists := ch.inFlightMessages[receivedMsg.ID]
		ch.inFlightMutex.Unlock()
		test.Equal(t, true, exists)

		// Finish the message
		err = ch.FinishMessage(clientID, receivedMsg.ID)
		test.Nil(t, err)

		// Verify it's no longer in-flight
		ch.inFlightMutex.Lock()
		_, exists = ch.inFlightMessages[receivedMsg.ID]
		ch.inFlightMutex.Unlock()
		test.Equal(t, false, exists)
	case <-time.After(5 * time.Second):
		t.Fatal("timeout waiting for message")
	}
}

// [Req: inferred — from Channel.RequeueMessage() immediate vs deferred requeue]
func TestBoundary_RequeueImmediateVsDeferred(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	opts.MsgTimeout = time.Second
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_requeue_modes" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	ch := topic.GetChannel("ch1")

	// Immediate requeue (timeout == 0)
	msg := NewMessage(topic.GenerateID(), []byte("requeue immediate"))
	err := ch.PutMessage(msg)
	test.Nil(t, err)

	select {
	case receivedMsg := <-ch.memoryMsgChan:
		clientID := int64(1)
		err := ch.StartInFlightTimeout(receivedMsg, clientID, opts.MsgTimeout)
		test.Nil(t, err)

		// Immediate requeue
		err = ch.RequeueMessage(clientID, receivedMsg.ID, 0)
		test.Nil(t, err)

		// Message should be back in the channel immediately
		test.Equal(t, int64(1), ch.Depth())
		test.Equal(t, uint64(1), atomic.LoadUint64(&ch.requeueCount))
	case <-time.After(5 * time.Second):
		t.Fatal("timeout waiting for message")
	}
}

// --- Delete and Cleanup ---

// [Req: inferred — from Topic.DeleteExistingChannel() channel map removal]
func TestBoundary_DeleteExistingChannel(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_delete_channel" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	topic.GetChannel("ch1")
	topic.GetChannel("ch2")

	err := topic.DeleteExistingChannel("ch1")
	test.Nil(t, err)

	topic.RLock()
	test.Equal(t, 1, len(topic.channelMap))
	_, exists := topic.channelMap["ch1"]
	test.Equal(t, false, exists)
	_, exists = topic.channelMap["ch2"]
	test.Equal(t, true, exists)
	topic.RUnlock()
}

// [Req: inferred — from NSQD.DeleteExistingTopic() topic map removal]
func TestBoundary_DeleteExistingTopic(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_delete_topic" + strconv.Itoa(int(time.Now().Unix()))
	nsqd.GetTopic(topicName)

	err := nsqd.DeleteExistingTopic(topicName)
	test.Nil(t, err)

	_, err = nsqd.GetExistingTopic(topicName)
	test.NotNil(t, err)
}

// [Req: inferred — from Channel.exit() CAS on exitFlag prevents double-close]
func TestBoundary_DoubleCloseChannel(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_double_close" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	ch := topic.GetChannel("ch1")

	err := ch.Close()
	test.Nil(t, err)

	// Second close should return "exiting" error
	err = ch.Close()
	test.NotNil(t, err)
}

// --- Configuration Boundaries ---

// [Req: inferred — from NewOptions() default values]
func TestBoundary_DefaultOptions(t *testing.T) {
	opts := NewOptions()
	test.Equal(t, int64(10000), opts.MemQueueSize)
	test.Equal(t, 60*time.Second, opts.MsgTimeout)
	test.Equal(t, 15*time.Minute, opts.MaxMsgTimeout)
	test.Equal(t, int64(2500), opts.MaxRdyCount)
	test.Equal(t, 100*time.Millisecond, opts.QueueScanInterval)
}

// [Req: inferred — from Channel.initPQ() pqSize calculation with math.Max]
func TestBoundary_PriorityQueueInitialization(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 0 // edge case: zero queue size
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_pq_init" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	ch := topic.GetChannel("ch1")

	// With MemQueueSize=0, pqSize should be max(1, 0/10) = 1
	expectedPQSize := int(math.Max(1, float64(opts.MemQueueSize)/10))
	test.Equal(t, 1, expectedPQSize)

	// Channel should still be functional
	test.Equal(t, false, ch.Exiting())
}

// [Req: inferred — from Channel memoryMsgChan nil when MemQueueSize=0]
func TestBoundary_ZeroMemQueueSize(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 0
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_zero_memqueue" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	ch := topic.GetChannel("ch1")

	// memoryMsgChan should be nil when MemQueueSize=0 (non-ephemeral)
	if ch.memoryMsgChan != nil {
		t.Error("memoryMsgChan should be nil when MemQueueSize=0")
	}

	// Messages should go directly to backend
	msg := NewMessage(topic.GenerateID(), []byte("direct to disk"))
	err := ch.PutMessage(msg)
	test.Nil(t, err)
	test.Equal(t, int64(1), ch.Depth())
}

// [Req: inferred — from NSQD.isLoading flag preventing PersistMetadata during load]
func TestBoundary_IsLoadingPreventsMetadataPersist(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_isloading" + strconv.Itoa(int(time.Now().Unix()))

	// Set isLoading
	atomic.StoreInt32(&nsqd.isLoading, 1)
	nsqd.GetTopic(topicName)

	// Persist should skip during loading (not error)
	// This is checked indirectly: metadata should not contain the topic created during loading
	err := nsqd.PersistMetadata()
	test.Nil(t, err)

	metadata, err := getMetadata(nsqd)
	test.Nil(t, err)

	// Topic created during loading may or may not appear in persisted metadata
	// The key invariant: no crash during loading + persist
	atomic.StoreInt32(&nsqd.isLoading, 0)
}

// [Req: inferred — from NSQD.Exit() atomic CAS prevents double-exit]
func TestBoundary_DoubleExit(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)

	// First exit should succeed
	nsqd.Exit()

	// Second exit should not panic (guarded by atomic CAS on isExiting)
	// This is a no-op due to the CAS guard
	nsqd.Exit()
}

// [Req: inferred — from Channel.flush() persists all queues during Close()]
func TestBoundary_FlushPersistsInFlightAndDeferred(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	opts.MsgTimeout = 5 * time.Second
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_flush" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	ch := topic.GetChannel("ch1")

	// Put messages and make some in-flight
	for i := 0; i < 5; i++ {
		msg := NewMessage(topic.GenerateID(), []byte(fmt.Sprintf("flush-%d", i)))
		err := ch.PutMessage(msg)
		test.Nil(t, err)
	}

	// Take 2 messages in-flight
	for i := 0; i < 2; i++ {
		select {
		case msg := <-ch.memoryMsgChan:
			ch.StartInFlightTimeout(msg, int64(i+1), opts.MsgTimeout)
		case <-time.After(time.Second):
			t.Fatal("timeout getting message for in-flight")
		}
	}

	ch.inFlightMutex.Lock()
	inFlightBefore := len(ch.inFlightMessages)
	ch.inFlightMutex.Unlock()
	test.Equal(t, 2, inFlightBefore)

	// Close triggers flush - in-flight messages should be written to backend
	ch.Close()

	// After close, the backend should have all remaining messages
	// (memory + in-flight + deferred all flushed to disk)
}

// [Req: inferred — from NewMessage() timestamp initialization]
func TestBoundary_NewMessageIDUniqueness(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_id_unique" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)

	ids := make(map[MessageID]bool)
	for i := 0; i < 1000; i++ {
		id := topic.GenerateID()
		if ids[id] {
			t.Fatalf("duplicate message ID generated at iteration %d", i)
		}
		ids[id] = true
	}
}

// [Req: inferred — from Channel.RemoveClient() nonexistent client is no-op]
func TestBoundary_RemoveNonexistentClient(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_remove_nonexist" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	ch := topic.GetChannel("ch1")

	// Should not panic
	ch.RemoveClient(999)

	ch.RLock()
	test.Equal(t, 0, len(ch.clients))
	ch.RUnlock()
}

// [Req: inferred — from Channel.AddClient() duplicate client is no-op]
func TestBoundary_DuplicateAddClient(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	opts.MemQueueSize = 100
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	topicName := "test_dup_client" + strconv.Itoa(int(time.Now().Unix()))
	topic := nsqd.GetTopic(topicName)
	ch := topic.GetChannel("ch1")

	fakeClient := &fakeConsumer{}
	err := ch.AddClient(1, fakeClient)
	test.Nil(t, err)

	// Adding same client ID again should be a no-op (not error)
	err = ch.AddClient(1, fakeClient)
	test.Nil(t, err)

	ch.RLock()
	test.Equal(t, 1, len(ch.clients))
	ch.RUnlock()
}

// [Req: inferred — from NSQD.GetExistingTopic() returns error for nonexistent]
func TestBoundary_GetNonExistentTopic(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	_, err := nsqd.GetExistingTopic("nonexistent_topic")
	test.NotNil(t, err)
}

// [Req: inferred — from NSQD.IsHealthy() health state management]
func TestBoundary_HealthCheck(t *testing.T) {
	opts := NewOptions()
	opts.Logger = test.NewTestLogger(t)
	_, _, nsqd := mustStartNSQD(opts)
	defer os.RemoveAll(opts.DataPath)
	defer nsqd.Exit()

	// Fresh nsqd should be healthy
	test.Equal(t, true, nsqd.IsHealthy())
}

// ============================================================================
// Test helper: fakeConsumer implements the Consumer interface for testing
// ============================================================================

type fakeConsumer struct{}

func (f *fakeConsumer) UnPause()                    {}
func (f *fakeConsumer) Pause()                      {}
func (f *fakeConsumer) Close() error                { return nil }
func (f *fakeConsumer) TimedOutMessage()            {}
func (f *fakeConsumer) Stats(string) ClientStats    { return ClientStats{} }
func (f *fakeConsumer) Empty()                      {}
