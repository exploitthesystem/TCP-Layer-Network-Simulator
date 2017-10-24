"""
* Author:      Marko Ljubicic
* Assignment:  PA 2 - A
* File:        StudentNetworkSimulator.py
* Date:        03/20/2017
* Description:
*              The alternating-bit version of a reliable
*              transport protocol.
"""

from NetworkSimulator import NetworkSimulator
from Queue import Queue
from Packet import Packet
from message import Message


class StudentNetworkSimulator(NetworkSimulator, object):
    """
     * Predefined Constants (static member variables):
     *
     *   int MAXDATASIZE : the maximum size of the Message data and
     *                     Packet payload
     *
     *   int A           : a predefined integer that represents entity A
     *   int B           : a predefined integer that represents entity B
     *
     *
     * Predefined Member Methods:
     *
     *  stopTimer(int entity):
     *       Stops the timer running at "entity" [A or B]
     *  startTimer(int entity, double increment):
     *       Starts a timer running at "entity" [A or B], which will expire in
     *       "increment" time units, causing the interrupt handler to be
     *       called.  You should only call this with A.
     *  toLayer3(int callingEntity, Packet p)
     *       Puts the packet "p" into the network from "callingEntity" [A or B]
     *  toLayer5(int entity, String dataSent)
     *       Passes "dataSent" up to layer 5 from "entity" [A or B]
     *  getTime()
     *       Returns the current time in the simulator.  Might be useful for
     *       debugging.
     *  printEventList()
     *       Prints the current event list to stdout.  Might be useful for
     *       debugging, but probably not.
     *
     *
     *  Predefined Classes:
     *
     *  Message: Used to encapsulate a message coming from layer 5
     *    Constructor:
     *      Message(String inputData):
     *          creates a new Message containing "inputData"
     *    Methods:
     *      boolean setData(String inputData):
     *          sets an existing Message's data to "inputData"
     *          returns true on success, false otherwise
     *      String getData():
     *          returns the data contained in the message
     *  Packet: Used to encapsulate a packet
     *    Constructors:
     *      Packet (Packet p):
     *          creates a new Packet that is a copy of "p"
     *      Packet (int seq, int ack, int check, String newPayload)
     *          creates a new Packet with a sequence field of "seq", an
     *          ack field of "ack", a checksum field of "check", and a
     *          payload of "newPayload"
     *      Packet (int seq, int ack, int check)
     *          chreate a new Packet with a sequence field of "seq", an
     *          ack field of "ack", a checksum field of "check", and
     *          an empty payload
     *    Methods:
     *      boolean setSeqnum(int n)
     *          sets the Packet's sequence field to "n"
     *          returns true on success, false otherwise
     *      boolean setAcknum(int n)
     *          sets the Packet's ack field to "n"
     *          returns true on success, false otherwise
     *      boolean setChecksum(int n)
     *          sets the Packet's checksum to "n"
     *          returns true on success, false otherwise
     *      boolean setPayload(String newPayload)
     *          sets the Packet's payload to "newPayload"
     *          returns true on success, false otherwise
     *      int getSeqnum()
     *          returns the contents of the Packet's sequence field
     *      int getAcknum()
     *          returns the contents of the Packet's ack field
     *      int getChecksum()
     *          returns the checksum of the Packet
     *      int getPayload()
     *          returns the Packet's payload
     *

     """

    # Add any necessary class/static variables here.  Remember, you cannot use
    # these variables to send messages error free!  They can only hold
    # state information for A or B.
    # Also add any necessary methods (e.g. checksum of a String)

    NetworkSimulator.senderQueue = Queue(1)
    NetworkSimulator.receiverQueue = Queue(1)
    NetworkSimulator.sequenceNumber = 0

    # Variables for statistical calculations

    lost = 0.0         # The number of lost packets
    corrupt = 0.0      # The number of corrupt packets
    successful = 0.0   # The number of successfully transmitted packets (not lost)
    total = 0.0        # The number of total packets sent and received by the protocol
    application = 0.0  # The number of packets sent to layer 5 of the application

    # Generates network statistics based on information stored in the variables above.
    def print_statistics(self):
        print("")
        print("")
        print("Packets lost: " + str(((self.lost - 1) / self.total) * 100) + "%")
        print("Packets corrupted: " + str((self.corrupt / self.total) * 2*100) + "%")
        print("Application packets: " + str(self.application))
        print("Successful packets: " + str(self.successful))
        print("Total packets: " + str(self.total))
        return

    @staticmethod
    def generate_checksum(packet):
        packet.set_checksum(packet.get_seqnum() + packet.get_acknum())
        packet.set_checksum(packet.get_checksum() + sum(bytearray(packet.get_payload())))

    def make_packet(self, message):
        pkt = Packet(self.sequenceNumber,
                     (len(str(message.get_data())) + self.sequenceNumber),
                     0,
                     str(message.get_data()))

        self.generate_checksum(pkt)
        self.sequenceNumber += len(message.get_data())

        return pkt

    # This is the constructor.  Don't touch!
    def __init__(self, num_messages, loss, corrupt, avg_delay, trace, seed):
        super(StudentNetworkSimulator, self).__init__(num_messages, loss, corrupt, avg_delay, trace, seed)

    # This routine will be called whenever the upper layer at the sender [A]
    # has a message to send.  It is the job of your protocol to insure that
    # the data in such a message is delivered in-order, and correctly, to
    # the receiving upper layer.
    def a_output(self, message):
        print("a_output was called.")
        self.total += 1
        # Lost count gets incremented in a_output; should get decremented in a_input.
        self.lost += 1

        # If the queue is full, ignore the incoming packet.
        if self.senderQueue.full():
            return

        pkt = self.make_packet(message)
        self.senderQueue.put(pkt)
        self.to_layer3(0, pkt)
        self.start_timer(0, 20)


    # This routine will be called whenever a packet sent from the B-side
    # (i.e. as a result of a toLayer3() being done by a B-side procedure)
    # arrives at the A-side.  "packet" is the (possibly corrupted) packet
    # sent from the B-side.
    def a_input(self, packet):
        print("a_input was called.")
        # Lost count gets decremented in a_input, indicating successful delivery
        # of corresponding a_output packet.
        self.lost -= 1

        if packet.get_seqnum() + packet.get_acknum() == packet.get_checksum():
            if not self.senderQueue.empty():
                self.senderQueue.get()
                self.stop_timer(0)
                self.successful += 1
        else:
            self.corrupt += 1

    # This routine will be called when A's timer expires (thus generating a
    # timer interrupt). You'll probably want to use this routine to control
    # the retransmission of packets. See startTimer() and stopTimer(), above,
    # for how the timer is started and stopped.

    def a_timer_interrupt(self):
        print("a_timer_interrupt was called.")
        pkt = self.senderQueue.get()
        self.senderQueue.put(pkt)
        self.lost += 1
        self.total += 1
        self.to_layer3(0, pkt)
        self.start_timer(0, 20)

    # This routine will be called once, before any of your other A-side
    # routines are called. It can be used to do any required
    # initialization (e.g. of member variables you add to control the state
    # of entity A).

    def a_init(self):
        pass

    # This routine will be called whenever a packet sent from the B-side
    # (i.e. as a result of a toLayer3() being done by an A-side procedure)
    # arrives at the B-side.  "packet" is the (possibly corrupted) packet
    # sent from the A-side.

    def b_input(self, packet):
        print("b_input was called.")
        packet_check_sum = packet.get_checksum()
        packet.set_checksum(packet.get_seqnum())
        self.generate_checksum(packet)
        self.total += 1

        # If packet is not corrupt...
        if packet_check_sum == packet.get_checksum():
            ack_packet = Packet(packet.get_seqnum(),
                                packet.get_acknum(),
                                packet.get_seqnum() + packet.get_acknum())
            self.generate_checksum(ack_packet)
            message = Message(str(packet.get_payload()))

            self.successful += 1

            # If queue is empty, extract and acknowledge the packet.
            if self.receiverQueue.empty():
                self.receiverQueue.put(ack_packet)
                self.application += 1
                self.to_layer5(1, message)
                self.to_layer3(1, ack_packet)
            else:
                previous_ack_packet = self.receiverQueue.get()
                self.receiverQueue.put(previous_ack_packet)

                if previous_ack_packet.get_seqnum() == packet.get_seqnum():
                    self.to_layer3(1, previous_ack_packet)
                else:
                    self.receiverQueue.get()
                    self.receiverQueue.put(ack_packet)
                    self.application += 1
                    self.to_layer5(1, message)
                    self.to_layer3(1, ack_packet)
        # Else packet is corrupt...
        else:
            self.corrupt += 1
            # If the packet is corrupt and the queue is empty (no previous packet has been received),
            # then perform no action. Wait for sender's timer to expire.
            if self.receiverQueue.empty():
                return
            # Else resend previously ACKed packet.
            else:
                previous_ack_packet = self.receiverQueue.get()
                self.receiverQueue.put(previous_ack_packet)
                self.to_layer3(1, previous_ack_packet)

    # This routine will be called once, before any of your other B-side
    # routines are called. It can be used to do any required
    # initialization (e.g. of member variables you add to control the state
    # of entity B).
    def b_init(self):
        pass
