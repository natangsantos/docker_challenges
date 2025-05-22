function launchChallenge(chal_id) {
    fetch(`/plugins/container_challenges/launch/${chal_id}`, {
        method: 'POST'
    })
    .then(res => res.json())
    .then(data => {
        if (data.url) {
            document.getElementById("container-url").innerHTML =
                `<a href="${data.url}" target="_blank">Access Challenge Instance</a>`;
        } else {
            alert("Failed to launch container.");
        }
    });
}
