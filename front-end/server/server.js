const fs = require('fs');
const bodyParser = require('body-parser');
const jsonServer = require('json-server');
const cors = require('cors');

const server = jsonServer.create();

const db = jsonServer.router('./server/db.json');

server.use(bodyParser.urlencoded({extended: true}));
server.use(bodyParser.json());

// server.use(cors());

/**
 * Use this function for a route if you need to do some server side processing.
 */
server.get('', (req, res) => {});

server.use(db);

server.listen(3000, () => {
  console.log('Run API Server');
  console.log('http://localhost:3000');
});
