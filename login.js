async function goToInstructions() {
    const name = document.getElementById("screen-name").value.trim();
    if (name === "") {
        alert("Please enter a screen name.");
        return;
    }

    try {
        const response = await fetch("http://localhost:8766/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ screen_name: name })
        });

        if (response.ok) {
            const data = await response.json();
            sessionStorage.setItem("player_id", data.player_id);
            sessionStorage.setItem("screen_name", name);
            window.location.href = `instructions.html`;
        } else {
            const errorText = await response.text();
            alert("Login failed: " + errorText);
        }
    } catch (error) {
        console.error("Error during login:", error);
        alert("Could not connect to the login server.");
    }
}

function goBack() {
    window.location.href = "index.html";
}