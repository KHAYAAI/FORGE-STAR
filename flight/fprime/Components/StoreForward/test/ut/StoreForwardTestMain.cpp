// ======================================================================
// \title  StoreForwardTestMain.cpp
// \brief  Test entry point for StoreForward
// ======================================================================
#include "StoreForwardTester.hpp"

TEST(Nominal, StoreAndDownlinkPass) { ForgeSat::StoreForwardTester t; t.testStoreAndDownlinkPass(); }
TEST(Nominal, NoDownlinkOutsidePass) { ForgeSat::StoreForwardTester t; t.testNoDownlinkOutsidePass(); }
TEST(OffNominal, BufferFullDropsAndWarns) { ForgeSat::StoreForwardTester t; t.testBufferFullDropsAndWarns(); }
TEST(OffNominal, ClearKeepsSequenceMoving) { ForgeSat::StoreForwardTester t; t.testClearKeepsSequenceMoving(); }

TEST(Nominal, PassPredictorInput) { ForgeSat::StoreForwardTester t; t.testPassPredictorInput(); }

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
