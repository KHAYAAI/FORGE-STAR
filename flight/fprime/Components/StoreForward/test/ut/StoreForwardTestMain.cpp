// ======================================================================
// \title  StoreForwardTestMain.cpp
// \brief  Test entry point for StoreForward
// ======================================================================
#include <memory>
#include "StoreForwardTester.hpp"  // testers live on the heap: the component holds a multi-MB store

TEST(Nominal, StoreAndDownlinkPass) { auto t = std::make_unique<ForgeSat::StoreForwardTester>(); t->testStoreAndDownlinkPass(); }
TEST(Nominal, NoDownlinkOutsidePass) { auto t = std::make_unique<ForgeSat::StoreForwardTester>(); t->testNoDownlinkOutsidePass(); }
TEST(OffNominal, BufferFullDropsAndWarns) { auto t = std::make_unique<ForgeSat::StoreForwardTester>(); t->testBufferFullDropsAndWarns(); }
TEST(OffNominal, ClearKeepsSequenceMoving) { auto t = std::make_unique<ForgeSat::StoreForwardTester>(); t->testClearKeepsSequenceMoving(); }

TEST(Nominal, PassPredictorInput) { auto t = std::make_unique<ForgeSat::StoreForwardTester>(); t->testPassPredictorInput(); }

TEST(Nominal, AcksDropStoredDuplicates) { auto t = std::make_unique<ForgeSat::StoreForwardTester>(); t->testAcksDropStoredDuplicates(); }

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
