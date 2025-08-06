document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("loginForm");

  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const username = document.getElementById("username").value;
      const password = document.getElementById("password").value;

      try {
        const response = await api.login(username, password);

        const result = await response.json();

        if (response.ok) {
          alert("Login successful");
          window.location.href = "dashboard.html";  // ✅ redirect to renamed file
        } else {
          alert(result.detail || "Login failed");
        }
      } catch (error) {
        console.error("Error:", error);
        alert("An error occurred");
      }
    });
  }
});
