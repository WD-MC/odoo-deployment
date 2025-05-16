def call(String registry, String image, List tags) {
    tags.each { tag ->
        def response = sh(
            script: "curl -s http://${registry}/v2/${image}/tags/list | grep '\"${tag}\"'",
            returnStatus: true
        )
        if (response == 0) {
            echo "✅ Tag '${tag}' présent dans ${registry}/${image}"
        } else {
            error("❌ Tag '${tag}' manquant dans ${registry}/${image}")
        }
    }
}