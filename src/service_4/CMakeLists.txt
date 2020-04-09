add_executable(
	service_4
	service_4.cpp
	${PROTO_SRCS}
	${GRPC_SRCS}
)

target_link_libraries(
	service_4
	gRPC::grpc++_reflection
	protobuf::libprotobuf
	jaegertracing
	nlohmann_json::nlohmann_json
)

install(TARGETS service_4 DESTINATION ./)
