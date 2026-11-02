set(SOURCE_FILES
  "${CMAKE_CURRENT_LIST_DIR}/PayloadSim.fpp"
  "${CMAKE_CURRENT_LIST_DIR}/PayloadSim.cpp"
)
set(MOD_DEPS Components_StoreForward)
register_fprime_module()
