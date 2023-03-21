#include "component_a.h"

extern int dummyLibInterface();

int dummyInterface(void) {
    return 0 + dummyLibInterface();
}