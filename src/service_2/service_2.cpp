#include <time.h>
#include <fstream>
#include <iostream>
#include <memory>
#include <mutex>
#include <nlohmann/json.hpp>
#include <string>
#include "../tracing.h"

#include <grpcpp/grpcpp.h>

#ifdef BAZEL_BUILD
#include "examples/protos/helloworld.grpc.pb.h"
#else
#include "helloworld.grpc.pb.h"
#endif

using namespace grpc;
using namespace helloworld;
using namespace std;
using json = nlohmann::json;
using std::chrono::microseconds;
using std::chrono::duration_cast;
using std::chrono::system_clock;

enum DistributionType { constant, log_normal };

struct rpc_params {
  DistributionType distribution_type;
  double pre_time_mean;
  double pre_time_std;
  double post_time_mean;
  double post_time_std;
  double proc_time_mean;
  double proc_time_std;
};

long getCurrentTime() {
  struct timeval tv;
  gettimeofday(&tv, NULL);
  return tv.tv_sec * 1000 + tv.tv_usec / 1000;
}

class CommonCallData {
 public:
  service_2::AsyncService* service_;
  ServerCompletionQueue* cq_;
  ServerContext ctx_;
  HelloRequest request_;
  HelloReply reply_;
  ServerAsyncResponseWriter<HelloReply> responder_;
  enum CallStatus { CREATE, PROCESS, FINISH, DESTROY };
  CallStatus status_;
  std::unique_ptr<opentracing::Span> span;
  explicit CommonCallData(service_2::AsyncService* service,
                          ServerCompletionQueue* cq)
      : service_(service), cq_(cq), responder_(&ctx_), status_(CREATE) {}
  virtual ~CommonCallData() {}
  virtual void Proceed(int ID = -1) = 0;
};

class AbstractAsyncClientCall {
 public:
  service_2::AsyncService* service_;
  Status status;
  ClientContext context;
  HelloRequest request;
  HelloReply reply;
  virtual ~AbstractAsyncClientCall() {}
  virtual void Proceed(bool = true) = 0;
};

class AsyncRpc_6_ClientCall : public AbstractAsyncClientCall {
 public:
  std::unique_ptr<ClientAsyncResponseReader<HelloReply>> responder;
  std::unique_ptr<opentracing::Span> span;
  CommonCallData* call_;
  int requestID;

  AsyncRpc_6_ClientCall(CompletionQueue& cq_,
                        std::unique_ptr<service_6::Stub>& stub_,
                        CommonCallData* call, int ID)
      : AbstractAsyncClientCall(), call_(call), requestID(ID) {
    std::map<std::string, std::string> writer_text_map;
    TextMapWriter writer(writer_text_map);
    span = opentracing::Tracer::Global()->StartSpan(
        "rpc_6_client", {opentracing::ChildOf(&((call_->span)->context()))});
    opentracing::Tracer::Global()->Inject(span->context(), writer);
    request.set_name(writer_text_map.begin()->second);
    responder = stub_->Asyncrpc_6(&context, request, &cq_);
    responder->Finish(&reply, &status, (void*)this);
  }

  virtual void Proceed(bool ok = true) override {
    span->Finish();
    GPR_ASSERT(ok);
    if (!status.ok()) {
      cout << "service_2 forward rpc_6 fail! Error code: ";
      cout << status.error_code() << ": " << status.error_message() << endl;
    }
    call_->Proceed(requestID);
    delete this;
  }
};

class Rpc_6_Client {
 private:
  std::unique_ptr<service_6::Stub> stub_;
  CompletionQueue cq_;

 public:
  explicit Rpc_6_Client(std::shared_ptr<Channel> channel)
      : stub_(service_6::NewStub(channel)) {}

  void Forward(CommonCallData* call, int ID) {
    AsyncRpc_6_ClientCall* call_ =
        new AsyncRpc_6_ClientCall(cq_, stub_, call, ID);
  }

  void AsyncCompleteRpc() {
    void* got_tag;
    bool ok = false;
    while (cq_.Next(&got_tag, &ok)) {
      AbstractAsyncClientCall* call =
          static_cast<AbstractAsyncClientCall*>(got_tag);
      call->Proceed(ok);
    }
    cout << "Rpc_6_Client Completion queue is shutting down." << endl;
  }
};

class Rpc_2_CallData : public CommonCallData {
 public:
  std::lognormal_distribution<double>* rpc_2_proc_dist_;
  std::default_random_engine gen;
  Rpc_6_Client* rpc_6_client_;
  bool sent[1] = {false};
  bool getResponse[1] = {false};
  std::mutex _mtx;
  Rpc_2_CallData(service_2::AsyncService* service, ServerCompletionQueue* cq,
                 std::lognormal_distribution<double>* rpc_2_proc_dist,
                 Rpc_6_Client* rpc_6_client)
      : CommonCallData(service, cq),
        rpc_2_proc_dist_(rpc_2_proc_dist),
        rpc_6_client_(rpc_6_client) {
    Proceed();
  }

  virtual void Proceed(int ID = -1) override {
    std::unique_lock<std::mutex> cv_lock(_mtx);
    try {
      if (status_ == CREATE) {
        status_ = PROCESS;
        service_->Requestrpc_2(&ctx_, &request_, &responder_, cq_, cq_, this);
        auto seed =
            duration_cast<microseconds>(system_clock::now().time_since_epoch())
                .count();
        gen = std::default_random_engine(seed);
      } else if (status_ == PROCESS) {
        new Rpc_2_CallData(service_, cq_, rpc_2_proc_dist_, rpc_6_client_);

        std::map<std::string, std::string> client_context_map;
        client_context_map.insert(
            pair<string, string>("uber-trace-id", request_.name()));
        TextMapReader reader(client_context_map);
        auto parent_span = opentracing::Tracer::Global()->Extract(reader);
        span = opentracing::Tracer::Global()->StartSpan(
            "rpc_2_server", {opentracing::ChildOf(parent_span->get())});

        double proc_time = (*rpc_2_proc_dist_)(gen);
        auto proc_t0 =
            duration_cast<microseconds>(system_clock::now().time_since_epoch())
                .count();
        while (true) {
          auto proc_t1 = duration_cast<microseconds>(
                             system_clock::now().time_since_epoch())
                             .count();
          if (proc_t1 - proc_t0 >= (int)(proc_time)) break;
        }

        rpc_6_client_->Forward(this, 0);
        sent[0] = true;

        status_ = FINISH;
      } else if (status_ == FINISH) {
        getResponse[ID] = true;

        if (getResponse[0]) {
          span->Finish();
          responder_.Finish(reply_, Status::OK, this);
          status_ = DESTROY;
        }
      } else {
        // GPR_ASSERT(status_ == DESTROY);
        delete this;
      }
    } catch (...) {
      cv_lock.unlock();
      return;
    }
    cv_lock.unlock();
  }
};

class ServerImpl final {
 public:
  std::unique_ptr<ServerCompletionQueue> cq_;
  std::unique_ptr<Server> server_;
  service_2::AsyncService service_;
  ~ServerImpl() {
    server_->Shutdown();
    cq_->Shutdown();
  }

  void Run() {
    json rpcs_json;
    json services_json;
    std::ifstream json_file;
    json_file.open("config/rpcs.json");
    if (json_file.is_open()) {
      json_file >> rpcs_json;
      json_file.close();
    } else {
      cout << "Cannot open rpcs_config.json" << endl;
      return;
    }
    json_file.open("config/services.json");
    if (json_file.is_open()) {
      json_file >> services_json;
      json_file.close();
    } else {
      cout << "Cannot open services_config.json" << endl;
      return;
    }

    int port = services_json["service_2"]["server_port"];
    string server_address("0.0.0.0:" + to_string(port));
    ServerBuilder builder;
    builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    builder.RegisterService(&service_);
    cq_ = builder.AddCompletionQueue();
    server_ = builder.BuildAndStart();
    std::cout << "Server listening on " << server_address << std::endl;

    std::string service_6_addr = services_json["service_6"]["server_addr"];
    int service_6_port = services_json["service_6"]["server_port"];

    // currently distribution type not use, if const set std = 0
    string tmp_rpc_2_distribution_type =
        rpcs_json["rpc_2"]["distribution_type"];
    DistributionType rpc_2_distribution_type;
    if (tmp_rpc_2_distribution_type == "log_normal")
      rpc_2_distribution_type = log_normal;
    else
      rpc_2_distribution_type = constant;
    rpc_params rpc_2_params = {
        rpc_2_distribution_type,
        rpcs_json["rpc_2"]["pre_time_mean"],
        rpcs_json["rpc_2"]["pre_time_std"],
        rpcs_json["rpc_2"]["post_time_mean"],
        rpcs_json["rpc_2"]["post_time_std"],
        rpcs_json["rpc_2"]["proc_time_mean"],
        rpcs_json["rpc_2"]["proc_time_std"],
    };
    std::lognormal_distribution<double> rpc_2_proc_dist;
    double rpc_2_proc_time_mean = rpc_2_params.proc_time_mean;
    if (rpc_2_proc_time_mean != 0) {
      double rpc_2_proc_time_std = rpc_2_params.proc_time_std;
      double rpc_2_proc_m = log(
          rpc_2_proc_time_mean /
          sqrt(1 + pow(rpc_2_proc_time_std, 2) / pow(rpc_2_proc_time_mean, 2)));
      double rpc_2_proc_s = sqrt(
          log(1 + pow(rpc_2_proc_time_std, 2) / pow(rpc_2_proc_time_mean, 2)));
      rpc_2_proc_dist =
          std::lognormal_distribution<double>(rpc_2_proc_m, rpc_2_proc_s);
    }

    Rpc_6_Client rpc_6_client(
        grpc::CreateChannel(service_6_addr + ":" + to_string(service_6_port),
                            grpc::InsecureChannelCredentials()));
    thread rpc_6_thread =
        thread(&Rpc_6_Client::AsyncCompleteRpc, &rpc_6_client);

    new Rpc_2_CallData(&service_, cq_.get(), &rpc_2_proc_dist, &rpc_6_client);

    void* tag;
    bool ok;
    while (true) {
      GPR_ASSERT(cq_->Next(&tag, &ok));
      GPR_ASSERT(ok);
      std::thread([=] {
        static_cast<CommonCallData*>(tag)->Proceed();
      }).detach();
    }
    rpc_6_thread.join();
  }
};

int main(int argc, char** argv) {
  SetUpTracer("config/jaeger-config.yml", "service_2");
  ServerImpl server;
  server.Run();
  return 0;
}
