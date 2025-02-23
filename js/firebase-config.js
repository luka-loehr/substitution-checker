// Import Firebase SDKs
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
import { getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";
import { getDatabase, ref, set, get } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-database.js";

// Firebase Konfiguration
const firebaseConfig = {
  apiKey: "AIzaSyBy228bRkP0vgDG6DFPy5etBxThb2Ene0s",
  authDomain: "vertretungsplan-checker.firebaseapp.com",
  projectId: "vertretungsplan-checker",
  storageBucket: "vertretungsplan-checker.firebasestorage.app",
  messagingSenderId: "98128959337",
  appId: "1:98128959337:web:85dbc6d6c4fa1f95924ff8"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const database = getDatabase(app);

export { auth, database, ref, set, get };
