class Application(object):
    def __init__(self):
        pass
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
        pass
