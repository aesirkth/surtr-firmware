#ifndef CIRCBUF_H
#define CIRCBUF_H

#include <stdint.h>

typedef struct {
    uint8_t *buffer;
    uint8_t head;
    uint8_t tail;
    uint8_t maxlen;

} Circbuf;


/**
 * ==========================================================
 * circbuf_push():
 *      Push 1 byte into circular buffer and step +1 MOD maxlen.
 *      Buffer is full if head+1 = tail
 */
uint8_t circbuf_push(Circbuf *circ, uint8_t byte_in);

/**
 * ==========================================================
 * circbuf_pop():
 *      Takes 1 byte from circular buffer and tail +1 MOD maxlen
 *      Buffer is empty if head = tail
 */
uint8_t circbuf_pop(Circbuf *circ, uint8_t *byte_out);

/**
 * ==========================================================
 * construct_circbuf():
 *      Initializes statically declared circbuf.
 */
void circbuf_construct(Circbuf *circbuf, uint8_t *buffer, const uint8_t maxlen);

#endif