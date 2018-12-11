const socket = new WebSocket("ws://localhost:8888/operation");
socket.onopen = function () {
};

socket.onclose = function () {
    alert('WebSocket closed');
};

socket.onmessage = function (event) {
    alert(event.data);
};

this.sendSocket = function() {
    let formEl = document.forms.formToSend;
    let formData = new FormData(formEl);
    object = {};
    for ([key, value] of formData) {
        object[key] = value;
    }
    socket.send(JSON.stringify(object));
}