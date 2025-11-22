const fs = require('fs');
const path = require('path');
const fetch = require('node-fetch');
const admin = require('firebase-admin');

// Load test credentials from functions/.env.local
const envPath = path.join(__dirname, '..', 'functions', '.env.local');
let params = {};
if (fs.existsSync(envPath)){
  const content = fs.readFileSync(envPath, 'utf8');
  content.split(/\r?\n/).forEach(line=>{
    line = line.trim(); if(!line || line.startsWith('#')) return;
    const idx = line.indexOf('='); if(idx === -1) return;
    let k = line.slice(0, idx).trim(); let v = line.slice(idx+1).trim();
    v = v.replace(/^\"|\"$/g, '');
    params[k]=v;
  });
}

const CLIENT_CODE = params.ANGELONE_CLIENT_CODE || 'AABL713311';
const PIN = params.ANGELONE_PASSWORD || '1012';
const TOTP = params.ANGELONE_TOTP_TOKEN || 'AGODKRXZZH6FHMYWMSBIK6KDXQ';

// API key extracted from firebase-debug.log (fallback from env FIREBASE_API_KEY)
const API_KEY = process.env.FIREBASE_API_KEY || 'AIzaSyAg6TvwNWGZwEfCP5ZVbszIIBBFHPaEinc';

(async ()=>{
  try{
    // Initialize Firebase Admin using ADC
    if (!admin.apps.length){
      admin.initializeApp();
    }
    const uid = 'test-runner-' + Math.random().toString(36).slice(2,9);
    console.log('Creating custom token for', uid);
    const customToken = await admin.auth().createCustomToken(uid);
    console.log('Custom token created (len):', customToken.length);

    // Exchange custom token for ID token
    const exchangeUrl = `https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=${API_KEY}`;
    const exchangeRes = await fetch(exchangeUrl, {
      method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({token: customToken, returnSecureToken: true})
    });
    const exchangeBody = await exchangeRes.text();
    console.log('Exchange status', exchangeRes.status, exchangeBody.slice(0,1000));
    if (exchangeRes.status !== 200){
      throw new Error('Failed to exchange custom token');
    }
    const exchangeJson = JSON.parse(exchangeBody);
    const idToken = exchangeJson.idToken;
    if (!idToken) throw new Error('No idToken in exchange response');
    console.log('Obtained idToken (len):', idToken.length);

    // POST to hosting endpoint
    const endpoint = 'https://tbsignalstream.web.app/api/directAngelLogin';
    console.log('POSTing to', endpoint);
    const postRes = await fetch(endpoint, {
      method: 'POST', headers: { 'Authorization': 'Bearer ' + idToken, 'Content-Type': 'application/json' },
      body: JSON.stringify({ clientCode: CLIENT_CODE, pin: PIN, totp: TOTP }), timeout: 30000
    });
    const postText = await postRes.text();
    console.log('POST status', postRes.status);
    try { console.log('POST JSON:', JSON.parse(postText)); } catch(e){ console.log('POST body text:', postText.slice(0,1000)); }

  }catch(err){
    console.error('Error during authenticated test:', err);
  }
})();
