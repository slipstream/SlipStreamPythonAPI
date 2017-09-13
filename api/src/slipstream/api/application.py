from deployment import RESOURCE_TYPE as dpl_resource_type

class Application(object):

    def __init__(self, client, app_id):
        self.client = client
        self.app_id = app_id

    def get(self, app_uri):
        pass

    def define(self, app_uri, definition):
        pass

    def deploy(self, app_uri):
        """

        :param app_uri:
        :return:
        POST on api/deployment
        {
"status" : 201,
"message" : "created deployment/dfd34916-6ede-47f7-aaeb-a30ddecbba5b",
"resource-id" : "deployment/dfd34916-6ede-47f7-aaeb-a30ddecbba5b"
}
        GET deployment/dfd34916-6ede-47f7-aaeb-a30ddecbba5b/start

(defn get-resource-op-url
  "Returns the URL for the given operation and collection within a channel."
  [{:keys [token cep] :as state} op url-or-id]
  (let [baseURI (:baseURI cep)
        url (cu/ensure-url baseURI url-or-id)
        opts (-> (cu/req-opts token)
                 (assoc :chan (create-op-url-chan op baseURI)))]
    (http/get url opts)))
        """
        # get app_uri as XML
        "module/examples/tutorials/service-testing/system/1940"
        deployment = {
            "id": "deployment/dfd34916-6ede-47f7-aaeb-a30ddecbba5b",
            "resourceURI": "http://sixsq.com/slipstream/1/Deployment",
            "module-resource-uri": app_uri,
            "category": "Deployment",
            "type": "Orchestration",
            "mutable": False,
            "nodes":
                {"node1":
                     {"parameters":
                          {"cloudservice": {},
                           "multiplicity": {"default-value": "3"}}},
                 "node2":
                     {"parameters":
                          {"cloudservice": {},
                           "multiplicity": {"default-value": "1"}}}}
        }
        self.client.add(dpl_resource_type, deployment)
