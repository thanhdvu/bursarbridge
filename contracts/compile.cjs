const fs = require('node:fs');
const solc = require('solc');
const names = ['AuditAnchor', 'CredentialRegistry', 'MandateGuard'];
const sources = Object.fromEntries(names.map(n => [n+'.sol', {content: fs.readFileSync(n+'.sol','utf8')}]));
const input = {language:'Solidity',sources,settings:{evmVersion:'paris',optimizer:{enabled:true,runs:200},outputSelection:{'*':{'*':['abi','evm.bytecode.object']}}}};
const output = JSON.parse(solc.compile(JSON.stringify(input)));
for (const error of output.errors || []) { if (error.severity === 'error') throw Error(error.formattedMessage); }
fs.mkdirSync('artifacts',{recursive:true});
for (const name of names) fs.writeFileSync('artifacts/'+name+'.json',JSON.stringify(output.contracts[name+'.sol'][name],null,2));
console.log('Compiled '+names.join(', ')+' with '+solc.version());
