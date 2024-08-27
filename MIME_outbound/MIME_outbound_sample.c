#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <linux/can.h>
#include <net/if.h>
#include <time.h>
#include <sys/time.h>
#include "functions.h"

// Function to construct MIME message payload
unsigned char* construct_mime_payload(const char* mime_type, const char* message_to_send, int* payload_length) {
    uint8_t mime_type_len = strlen(mime_type);
    uint32_t message_len = strlen(message_to_send);
    *payload_length = 2 + mime_type_len + 4 + message_len;

    unsigned char* total_payload = (unsigned char*)malloc(*payload_length);
    if (total_payload == NULL) {
        fprintf(stderr, "Memory allocation failed\n");
        return NULL;
    }

    int index = 0;
    total_payload[index++] = 0x00;
    total_payload[index++] = (unsigned char)mime_type_len;

    for (int i = 0; i < mime_type_len; i++) {
        total_payload[index++] = (unsigned char)mime_type[i];
    }

    // little-endian byte length conversion
    total_payload[index++] = (unsigned char)(message_len & 0xFF);
    total_payload[index++] = (unsigned char)((message_len >> 8) & 0xFF);
    total_payload[index++] = (unsigned char)((message_len >> 16) & 0xFF);
    total_payload[index++] = (unsigned char)((message_len >> 24) & 0xFF);

    for (int i = 0; i < message_len; i++) {
        total_payload[index++] = (unsigned char)message_to_send[i];
    }

    printf("\nHere is the MIME Rx payload:\n01 00 00\n");
    for (int i = 0; i < *payload_length; i++) {
        printf("%02X ", total_payload[i]);
        if ((i + 1) % 8 == 0) {
            printf("\n");
        }
    }
    if (*payload_length % 8 != 0) {
        printf("\n");
    }
    printf("01 00 01\n\n");

    return total_payload;
}

// Function to handle CAN messages
void handle_can_message(int sockfd, struct can_frame *frame, int *messaging_index, int *mime_index, int *payload_length, unsigned char* total_payload, int* payload_sent, int *tx_ack_index) {
    static struct can_frame last_frame;
    static int first_message = 1;

    if (!first_message) {
        classify_can_frame(frame, &last_frame);
    } else {
        first_message = 0;
        classify_can_frame(frame, frame);
    }

    last_frame = *frame;

    if ((frame->can_id & CAN_EFF_MASK) == 0x00010000) {
        if (*messaging_index == 0) {
            uint8_t payload[] = {0x01, 0x01, 0x00, 0x12, 0x16, 0x00, 0x00, 0x9A};
            send_can_frame(sockfd, 0x0002ABCD, payload, sizeof(payload));
            printf("Poll Response (Handshake)\n");
        } else {
            uint8_t payload[] = {0x00};
            send_can_frame(sockfd, 0x0002ABCD, payload, sizeof(payload));
            printf("Poll Response\n");
        }
        (*messaging_index)++;
    } else if ((frame->can_id & CAN_EFF_MASK) == 0x0014ABCD) {
        if (*messaging_index == 3) {
            uint8_t payload[] = {0x01, 0x01, 0x70, 0x10, 0x01, 0x00};
            send_can_frame(sockfd, 0x001DABCD, payload, sizeof(payload));
            printf("Send External Device ID\n");
        } else if ((*messaging_index > 3) && (*mime_index == 0)) {
            uint8_t payload[] = {0x01, 0x00, 0x00};
            send_can_frame(sockfd, 0x0025ABCD, payload, sizeof(payload));
            printf("MIME-1 (Beginning Packet Wrapper)\n");
            (*mime_index)++;
        } else if ((*messaging_index > 3) && (*mime_index <= (*payload_length / 8 + 1))) {
            uint8_t frame_length = (*payload_length - *payload_sent) >= 8 ? 8 : (*payload_length - *payload_sent);
            uint8_t *payload = (uint8_t *)malloc(frame_length * sizeof(uint8_t));
            if (payload == NULL) {
                perror("payload malloc");
                return;
            }

            int payload_sent_current_iteration = 0;
            for (int i = *payload_sent; i < *payload_sent + frame_length; i++) {
                if (i < *payload_length) {
                    payload[payload_sent_current_iteration++] = total_payload[i];
                }
            }

            send_can_frame(sockfd, 0x000CABCD, payload, frame_length);
            (*payload_sent) += payload_sent_current_iteration;
            (*mime_index)++;
            printf("MIME-%d (MIME Rx)\n", *mime_index);
            free(payload);
        } else if (*mime_index == (*payload_length / 8 + 2)) {
            uint8_t payload[] = {0x01, 0x00, 0x01};
            send_can_frame(sockfd, 0x0025ABCD, payload, sizeof(payload));
            (*mime_index)++;
            printf("MIME-%d (Ending Packet Wrapper)\n", *mime_index);
        }
        (*messaging_index)++;
    } else if (((frame->can_id & CAN_EFF_MASK) == 0x001CABCD) && (frame->data[0] == 0x00) && (frame->data[1] == 0x00)) {
        printf("\033[93mWARNING: Modem transmission failed. This typically indicates that it is not connected. The MIME content was not transferred.\033[0m\n");
    } else if ((frame->can_id & CAN_EFF_MASK) == 0x000BABCD) {
        (*tx_ack_index)++;
        if (*tx_ack_index == 2) {
            printf("\033[92mSUCCESS! The MyGeotab database has received the MIME message and it can be pulled via API.\033[0m\n");
        }
    }
}

int main() {
    int sockfd;
    struct sockaddr_can addr;
    int nbytes;
    struct can_frame frame;
    int messaging_index = 0;
    int mime_index = 0;
    int payload_sent = 0;
    int tx_ack_index = 0;
    const char* mime_type = "text/plain";
    const char* message_to_send = "This is a test MIME message that will be sent from the GO9 to the MyG cloud.";

    printf("\n== MIME Outbound Custom Messaging Sample ==\n");
    printf("This script sends a MIME message of custom type and content from the GO device to the MyG server.\n");

    printf("\nMIME Type: %s\n", mime_type);
    printf("MIME Payload: %s\n", message_to_send);

    int payload_length;
    unsigned char* total_payload = construct_mime_payload(mime_type, message_to_send, &payload_length);
    if (total_payload == NULL) {
        return 1;
    }

    setup_can_interface();

    if ((sockfd = socket(PF_CAN, SOCK_RAW, CAN_RAW)) < 0) {
        perror("socket");
        return 1;
    }

    int ifindex = get_can_interface_index(sockfd);
    addr.can_family = AF_CAN;
    addr.can_ifindex = ifindex;
    if (bind(sockfd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind");
        return 1;
    }

    printf("Commencing communication session logging...\n\n");
    printf("Direction |          DateTime          |    ArbID   | DLC |       Data       | Description\n");
    printf("--------- | -------------------------- | ---------- | --- | ---------------- | --------------\n");

    while (1) {
        nbytes = read(sockfd, &frame, sizeof(frame));
        if (nbytes < 0) {
            perror("read");
            return 1;
        }

        if (nbytes == sizeof(frame)) {
            print_can_frame(&frame);
            handle_can_message(sockfd, &frame, &messaging_index, &mime_index, &payload_length, total_payload, &payload_sent, &tx_ack_index);
        }
    }

    free(total_payload);
    close(sockfd);
    return 0;
}