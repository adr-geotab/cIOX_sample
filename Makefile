# Compiler and flags
CC = gcc
CFLAGS = -Wall -I. # -I. to include the current directory for header files

# Source files and objects
SRC = functions.c
OBJ = functions.o

# Targets
all: exc_idle_communication_template exc_iox_data_request exc_iox_data_request2

# Rules to build the executables
exc_idle_communication_template: idle_communication_template.o $(OBJ)
	$(CC) -o $@ idle_communication_template.o $(OBJ)

exc_iox_data_request: GO_IOX_data_transfer/iox_data_request.o $(OBJ)
	$(CC) -o $@ GO_IOX_data_transfer/iox_data_request.o $(OBJ)

exc_iox_data_request2: GO_IOX_data_transfer/iox_data_request2.o $(OBJ)
	$(CC) -o $@ GO_IOX_data_transfer/iox_data_request2.o $(OBJ)

# Rule to compile idle_communication_template.o
idle_communication_template.o: idle_communication_template.c functions.h
	$(CC) $(CFLAGS) -c idle_communication_template.c -o idle_communication_template.o

# Rule to compile GO_IOX_data_request.o
GO_IOX_data_request.o: GO_IOX_data_transfer/iox_data_request.c functions.h
	$(CC) $(CFLAGS) -c GO_IOX_data_transfer/iox_data_request.c -o GO_IOX_data_request.o

# Rule to compile GO_IOX_data_request2.o
GO_IOX_data_request2.o: GO_IOX_data_transfer/iox_data_request2.c functions.h
	$(CC) $(CFLAGS) -c GO_IOX_data_transfer/iox_data_request2.c -o GO_IOX_data_request2.o

# Clean up build files
clean:
	rm -f *.o GO_IOX_data_transfer/*.o exc_idle_communication_template exc_iox_data_request exc_iox_data_request2