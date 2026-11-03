set(LIBFORGE "${CMAKE_CURRENT_LIST_DIR}/../../../libforge")
set(SOURCE_FILES
  "${CMAKE_CURRENT_LIST_DIR}/PassPredictor.fpp"
  "${CMAKE_CURRENT_LIST_DIR}/PassPredictor.cpp"
  "${LIBFORGE}/src/forge_orbit.c"
)
set(MOD_DEPS Components_StoreForward)
register_fprime_module()
target_include_directories(${FPRIME_CURRENT_MODULE} PUBLIC "${LIBFORGE}/include")
target_link_libraries(${FPRIME_CURRENT_MODULE} PUBLIC m)
