function toggleAuthFields() {
    const method = document.getElementById("auth_method").value;
    document.getElementById("refresh_token_fields").style.display = method === "refresh_token" ? "block" : "none";
    document.getElementById("client_credentials_fields").style.display = method === "client_credentials" ? "block" : "none";
}

async function testConnection(connectionId) {
    const target = document.getElementById(`test-result-${connectionId}`);
    target.textContent = "Testing...";
    const response = await fetch(`/connections/${connectionId}/test`, { method: "POST" });
    target.innerHTML = await response.text();
}
