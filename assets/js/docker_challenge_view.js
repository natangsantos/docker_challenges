CTFd._internal.challenge.data = undefined
CTFd._internal.challenge.renderer = CTFd.lib.markdown();

function mergeQueryParams(params, query) {
    query = query || window.location.search;
    let obj = {};
    if (query) {
        query.substring(1).split('&').map(item => {
            let [k, v] = item.split('=');
            v = v ? decodeURIComponent(v.replace(/\+/g, ' ')) : '';
            obj[k] = v;
        });
    }
    Object.assign(obj, params);
    let arr = [];
    for (let k in obj) {
        if (obj.hasOwnProperty(k) && obj[k] !== undefined && obj[k] !== null) {
            arr.push(encodeURIComponent(k) + '=' + encodeURIComponent(obj[k]));
        }
    }
    return arr.join('&');
}

function displayStatus(message, isError = false, connectionInfoHtml = null) {
    const statusDiv = document.getElementById('instance-status');
    const errorDiv = document.getElementById('instance-error');
    const statusMessageSpan = document.getElementById('status-message');
    const errorMessageSpan = document.getElementById('error-message');
    const connectionInfoDiv = document.getElementById('connection-info');
    const startButton = document.getElementById('start-instance-btn');

    statusDiv.style.display = 'none';
    errorDiv.style.display = 'none';
    connectionInfoDiv.innerHTML = '';
    startButton.disabled = false;
    startButton.textContent = 'Start Instance';

    if (isError) {
        errorMessageSpan.textContent = message;
        errorDiv.style.display = 'block';
    } else {
        statusMessageSpan.textContent = message;
        if (connectionInfoHtml) {
            connectionInfoDiv.innerHTML = connectionInfoHtml;
        }
        statusDiv.style.display = 'block';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const startButton = document.getElementById('start-instance-btn');
    const challengeId = startButton.getAttribute('data-challenge-id');
    const apiUrl = CTFd.config.urlRoot + `/plugins/ctfd_docker_manager/api/start_instance/${challengeId}`;

    startButton.addEventListener('click', () => {
        startButton.disabled = true;
        startButton.textContent = 'Starting...';
        displayStatus('Requesting instance...', false);

        CTFd.fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'CSRF-Token': CTFd.config.csrfNonce
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayStatus(data.message, false, data.display_html);
                // Optionally disable button after successful start or change text
                startButton.textContent = 'Instance Running';
                // Maybe add a stop button dynamically here?
            } else {
                displayStatus(data.message, true);
                startButton.textContent = 'Start Instance'; // Re-enable on error
                startButton.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error starting instance:', error);
            displayStatus('An unexpected client-side error occurred.', true);
            startButton.textContent = 'Start Instance'; // Re-enable on error
            startButton.disabled = false;
        });
    });

    // Initial state (maybe check if an instance is already running? Requires backend changes)
    // displayStatus('Click button to start instance.');
});

