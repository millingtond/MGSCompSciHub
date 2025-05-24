// frontend/src/services/firebase.js
import { initializeApp } from "firebase/app";
import { 
  getAuth, 
  OAuthProvider, // Generic OAuth provider
  GoogleAuthProvider, // Example if you want Google too
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  updateProfile
} from "firebase/auth";

// TODO: Replace with your web app's Firebase configuration
// You get this from the Firebase console when you add a web app to your project.
const firebaseConfig = {
  apiKey: "AIzaSyAIxoh3MBfG0dc93f5G9J5l5jerQOmkVDA",
  authDomain: "mgscompscihub.firebaseapp.com",
  projectId: "mgscompscihub",
  storageBucket: "mgscompscihub.firebasestorage.app",
  messagingSenderId: "1057630378788",
  appId: "1:1057630378788:web:cca63fc56de6dcbf78f1b1"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// --- Microsoft Provider Setup ---
// Ensure you have enabled Microsoft as a sign-in provider in your Firebase project console
// and configured it with the Client ID and Client Secret from your Azure AD app registration.
const microsoftProvider = new OAuthProvider('microsoft.com');
// Optional: Specify tenant or custom parameters
// microsoftProvider.setCustomParameters({
//   // tenant: 'common', 
//   // tenant: 'organizations', 
//   // tenant: 'YOUR_AZURE_TENANT_ID.onmicrosoft.com' 
// });
microsoftProvider.addScope('user.read');
microsoftProvider.addScope('email');
microsoftProvider.addScope('openid');
microsoftProvider.addScope('profile');


// --- Google Provider Setup (Example, if you want to add it later) ---
// const googleProvider = new GoogleAuthProvider();
// googleProvider.addScope('profile');
// googleProvider.addScope('email');

export { 
  auth, 
  microsoftProvider,
  // googleProvider, // Uncomment if you use it
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  updateProfile
};
