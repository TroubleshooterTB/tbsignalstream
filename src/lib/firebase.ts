import { initializeApp, getApps } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import { getFunctions } from "firebase/functions";

// Firebase configuration - using the correct API key from Firebase console
const firebaseConfig = {
  apiKey: "AIzaSyDy8-a3NsAju5z3JwHLF9nDtHCADkeHHDE",
  authDomain: "tbsignalstream.firebaseapp.com",
  projectId: "tbsignalstream",
  storageBucket: "tbsignalstream.firebasestorage.app",
  messagingSenderId: "818546654122",
  appId: "1:818546654122:web:65f07943cd0c99081509d3",
  measurementId: "G-826MDT13SD"
};

// Initialize Firebase
let app;
if (getApps().length === 0) {
  app = initializeApp(firebaseConfig);
} else {
  app = getApps()[0];
}

export const auth = getAuth(app);
export const db = getFirestore(app);
export const functions = getFunctions(app, 'us-central1');
export default app;
