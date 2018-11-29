console.log("Starting inventory application");

var db = new PouchDB('inventory');

window.onload = function() {
    var app = new Vue({
        el: '#app',
        data: {
            message: 'Hello World!'
        }
    });
};
