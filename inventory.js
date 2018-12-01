console.log("Starting inventory application");

var db = new PouchDB('inventory');

var remoteDB = new PouchDB('http://localhost:5984/magfest');
db.sync(remoteDB, {
    live: true,
    retry: true
});

window.onload = function() {
    Vue.use(VueMaterial.default);

    var app = new Vue({
        el: '#app',
        data: {
            bins: {},
            departments: [],
            pallets: [],
            showAddDialog: false,
            editBin: {},
        },
        mounted() {
            db.changes({
                since: 'now',
                live: true,
                include_docs: true
            }).on('change', function(change) {
                if (change.deleted) {
                    console.log("Deleted: ", change);
                } else {
                    console.log("Changed: ", change);
                }
            });

            var self = this;
            db.get('departments').then(function(doc){
                self.departments = doc.departments;
                self.departments.forEach(function(department) {
                    self.$set(self.bins, department, []);
                    db.find({
                        selector: {
                            department: department,
                            type: 'bin'
                        },
                        sort: ['_id']
                    }).then(function(result) {
                        result.docs.forEach(function(bin) {
                            console.log("Found bin: ", bin);
                            self.bins[department].push(bin);
                        });
                    });
                });
            })
        },
        methods: {
            add_bin() {
                this.editBin = {};
                this.showAddDialog = true;
            },
            edit_bin(bin) {
                this.editBin = bin;
                this.showAddDialog = true;
            },
            save_bin(bin) {
                this.showAddDialog = false;
            },
            cancel_bin(bin) {
                this.showAddDialog = false;
                this.editBin = {};  
            },
            delete_bin(bin) {

            },
            add_item() {
                this.editBin.items.push([0, "New Item"]);
            },
            delete_item(item) {
                this.editBin.items.splice(this.editBin.items.indexOf(item), 1);
            }
        }
    });
};
