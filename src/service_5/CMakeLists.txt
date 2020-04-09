add_executable(
	service_5
	service_5.cpp
	${PROTO_SRCS}
	${GRPC_SRCS}
)

target_link_libraries(
	service_5
	gRPC::grpc++_reflection
	protobuf::libprotobuf
	jaegertracing
	nlohmann_json::nlohmann_json
)

install(TARGETS service_5 DESTINATION ./)
