document.addEventListener('DOMContentLoaded', function() {
    // Handle container stop buttons
    document.querySelectorAll('.stop-container').forEach(button => {
        button.addEventListener('click', function() {
            const containerId = this.dataset.id;
            const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
            
            fetch(`/admin/docker/containers/${containerId}/stop`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.closest('tr').remove();
                } else {
                    alert('Error stopping container: ' + data.error);
                }
            });
        });
    });

    // Auto-refresh container list every 30 seconds
    setInterval(() => {
        fetch('/admin/docker/containers')
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const newDoc = parser.parseFromString(html, 'text/html');
                const newTable = newDoc.querySelector('.table');
                document.querySelector('.table').innerHTML = newTable.innerHTML;
            });
    }, 30000);
});