#include <stdint.h>
#include <stdatomic.h>

extern _Atomic int32_t target_motor1;
extern _Atomic int32_t target_motor2;

extern _Atomic int32_t current_motor1;
extern _Atomic int32_t current_motor2;

void stepper_thread(void *p1, void *p2, void *p3);