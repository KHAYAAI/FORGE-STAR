set(LIBFORGE "${CMAKE_CURRENT_LIST_DIR}/../../../libforge")
set(SOURCE_FILES
  "${CMAKE_CURRENT_LIST_DIR}/CmdAuth.fpp"
  "${CMAKE_CURRENT_LIST_DIR}/CmdAuth.cpp"
  "${LIBFORGE}/src/forge_auth.c"
)
register_fprime_module()
target_include_directories(${FPRIME_CURRENT_MODULE} PUBLIC "${LIBFORGE}/include")
