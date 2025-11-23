// Función para autocompletar campos de inicio de sesión sin debug
function autocompletar(tipo) {
    const usuarios = window.usuarios_predeterminados || {};
    if (!usuarios[tipo]) {
        return;
    }
    const usernameInput = document.querySelector('input[name="username"]');
    const passwordInput = document.querySelector('input[name="password"]');
    if (usernameInput) {
        usernameInput.value = usuarios[tipo].email;
    }
    if (passwordInput) {
        passwordInput.value = usuarios[tipo].password;
    }
}
