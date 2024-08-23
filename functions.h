#ifndef FUNCTIONS_H
#define FUNCTIONS_H

#include <linux/can.h>

// Function prototypes
void send_can_frame(int sockfd, uint32_t id, uint8_t *data, size_t len);
void setup_can_interface(void);
int get_can_interface_index(int sockfd);
void print_can_frame(const struct can_frame *frame);
void classify_can_frame(const struct can_frame *inbound_frame, const struct can_frame *prev_outbound_frame);

#endif // FUNCTIONS_H