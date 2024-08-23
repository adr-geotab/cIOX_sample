#ifndef FUNCTIONS_H
#define FUNCTIONS_H

#include <linux/can.h>
#include <stdint.h>
#include <stddef.h>

// Function prototypes
int is_can_interface_up(void);
void setup_can_interface(void);
int get_can_interface_index(int sockfd);
void send_can_frame(int sockfd, uint32_t can_id, uint8_t *data, size_t data_len);
void print_can_frame(struct can_frame *frame);

#endif
