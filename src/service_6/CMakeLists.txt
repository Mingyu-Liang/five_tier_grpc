add_executable(
	service_6
	service_6.cpp
	${PROTO_SRCS}
	${GRPC_SRCS}
)

target_link_libraries(
	service_6
	gRPC::grpc++_reflection
	protobuf::libprotobuf
	jaegertracing
	nlohmann_json::nlohmann_json
)

install(TARGETS service_6 DESTINATION ./)
