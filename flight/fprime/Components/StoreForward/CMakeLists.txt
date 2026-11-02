set(LIBFORGE "${CMAKE_CURRENT_LIST_DIR}/../../../libforge")
set(SOURCE_FILES
  "${CMAKE_CURRENT_LIST_DIR}/StoreForward.fpp"
  "${CMAKE_CURRENT_LIST_DIR}/StoreForward.cpp"
  "${LIBFORGE}/src/forge.c"
)
register_fprime_module()
target_include_directories(${FPRIME_CURRENT_MODULE} PUBLIC "${LIBFORGE}/include")

set(UT_SOURCE_FILES
  "${CMAKE_CURRENT_LIST_DIR}/StoreForward.fpp"
  "${CMAKE_CURRENT_LIST_DIR}/test/ut/StoreForwardTestMain.cpp"
  "${CMAKE_CURRENT_LIST_DIR}/test/ut/StoreForwardTester.cpp"
)
set(UT_MOD_DEPS "${FPRIME_CURRENT_MODULE}")
set(UT_AUTO_HELPERS ON)
register_fprime_ut()
