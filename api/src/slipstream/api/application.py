from .module import Module


class Application(Module):
    def __init__(self, cimi, uri=None):
        """

        :param cimi: CIMI cimi
        :param uri:
        """
        super(Application, self).__init__(cimi, uri)

    def deploy(self, uri):
        """
        1. GET deployment template
        2. Set application and deployment parameters
           DeploymentTemplate {module: app_uri, cloud: cloud, ...}
        3. POST deployment document on /deployment - returns deployment/UUID id
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
        raise NotImplementedError()

