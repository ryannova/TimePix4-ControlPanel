/**
 * Generate very simple packet frames over the network.
 * Packets has the following format
 * 4 byte packet number
 * image frame
 */

#include <stdlib.h>
#include <stdio.h>
#include <iostream>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <signal.h>
#include <errno.h>

#define HEADER_SIZE 4
#define FRAME_SIZE 128*128
#define PACKET_SIZE FRAME_SIZE + HEADER_SIZE
#define PIXEL_FLIPS 1000

#define IP_ADDRESS "127.0.0.1"
#define PORT 7686
#define DATA_RATE 100


void INThandler(int signum) {
    exit(0);
}

int main(int argc, char *argv[]){
    signal(SIGINT, INThandler);
    /**
     * Creating socket to send packets over network
     */
    int sockfd;
    char buffer[PACKET_SIZE];
    struct sockaddr_in serv_addr;

    if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0){
        perror("Socket creation failed\n");
        exit(EXIT_FAILURE);
    }

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(PORT);
    serv_addr.sin_addr.s_addr = inet_addr(IP_ADDRESS);

    socklen_t addrLength = sizeof(serv_addr);
    printf("Sending data frames to %s on port %i\n", IP_ADDRESS, PORT);


    /**
     * Generating packets to be sent over the network
     */

    memset(buffer, 0, sizeof(buffer));

    while(true){
        if (sendto(sockfd, buffer, PACKET_SIZE, 0, (struct sockaddr *) &serv_addr, addrLength) < 0){
            printf("Failed to send packets.\n Error %i %s\n",
                errno,
                strerror(errno));
        }
        buffer[0] += 1;
        for (int i = 0; i < PIXEL_FLIPS; i++){
            int index = (rand() % (FRAME_SIZE)) + HEADER_SIZE;
            int value = rand() % 255;
            buffer[index] = value;
        }
        sleep(0.5);
    }

    

    

}