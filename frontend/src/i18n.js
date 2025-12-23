import { reactive, computed } from 'vue';

const currentLang = reactive({ value: 'en' });

const translations = {
    en: {
        // Auth
        loginTitle: "NetOps Flow",
        loginSubtitle: "Enterprise Network Automation",
        username: "Username",
        password: "Password",
        signIn: "Sign In",
        accessGranted: "Access Granted",
        accessDenied: "Access Denied",
        welcomeBack: "Welcome back.",
        authOnly: "Authorized Access Only",

        // Sidebar
        dashboard: "Dashboard",
        network: "Network",
        ipam: "IPAM",
        topology: "Topology",
        automation: "Automation",
        scriptRunner: "Script Runner",
        system: "System",
        settings: "Settings",
        logout: "Logout",

        // Dashboard
        totalSubnets: "Total Subnets",
        activeIps: "Active IPs",
        scripts: "Scripts",
        executions: "Executions",
        quickActions: "Quick Actions",
        systemStatus: "System Status",
        dbConnected: "Database Connected",
        workerActive: "Worker Active",
        newSubnet: "New Subnet",
        uploadScript: "Upload Script",

        // IPAM
        cidr: "CIDR",
        name: "Name",
        description: "Description",
        actions: "Actions",
        scanSubnet: "Scan Subnet",
        addIp: "Add IP",
        allocatedIps: "Allocated IPs in",
        address: "Address",
        hostname: "Hostname",
        mac: "MAC Address",
        lastScan: "Last Scan",
        status: "Status",
        noIps: "No IPs allocated or found yet. Click the Scan button.",
        save: "Save",
        cancel: "Cancel",
        allocate: "Allocate",
        manualIpAllocation: "Manual IP Allocation",
        ipAddress: "IP Address",
        subnetCreated: "Subnet Created",
        ipAllocated: "IP Allocated",
        scanStarted: "Scan Started",
        addressesFound: "addresses found",
        success: "Success",
        failedCreateSubnet: "Failed to create subnet",
        failedAllocateIp: "Failed to allocate IP",
        failedStartScan: "Failed to start scan",
        scanningBackground: "Scanning in background...",

        // Scripts
        uploadTitle: "Upload Script",
        availableScripts: "Available Scripts",
        executionHistory: "Execution History",
        clickDrag: "Click or drag file here",
        targetServer: "Target Server",
        localhost: "Localhost (Worker)",
        leaveEmpty: "Leave empty to run on the worker container.",
        runNow: "Run Now",
        enterPasswordConfirm: "Confirm Password to Execute",
        type: "Type",
        executionLog: "Execution Log",
        stdout: "STDOUT",
        stderr: "STDERR",
        uploaded: "Uploaded",
        error: "Error",
        started: "Started",
        scriptQueued: "Script execution queued",
        executionFailed: "Execution Failed",
        passwordRequired: "Password Required",
        confirmPasswordDetail: "Please confirm your password to execute.",
        deleted: "Deleted",
        scriptDeleted: "Script deleted successfully",
        scriptArgs: "Script Arguments",
        scriptArgsPlaceholder: "e.g. --verbose -n 5",
        fileSize: "File size",
        bytes: "bytes",
        invalidFileType: "Invalid file type. Only .py, .sh, .ps1 allowed.",
        stop: "Stop",
        deleteHistory: "Delete History",
        historyDeleted: "History Deleted",
        executionStopped: "Execution Stopped",
        accessDeniedTitle: "Access Denied",
        invalidPassword: "Invalid Password",
        invalidPasswordDetail: "The password you entered is incorrect.",
        confirmDeleteHistory: "Are you sure you want to delete the entire execution history?",
        confirmDeleteScript: "Are you sure you want to delete",

        // Settings
        myProfile: "My Profile",
        updatePassword: "Update Password",
        newPassword: "New Password",
        userManagement: "User Management",
        serverInventory: "Server Inventory",
        newUser: "New User",
        newServer: "New Server",
        role: "Role",
        permissions: "Permissions",
        saveUser: "Save User",
        saveServer: "Save Server",
        viewTopo: "View Topology",
        runScripts: "Run Scripts",
        accessSettings: "Access Settings",
        accessIpam: "Access IPAM",

        // User Management
        deleteUser: "Delete User",
        confirmDeleteUser: "Are you sure you want to delete user",
        userDeleted: "User deleted successfully",
        cannotDeleteSelf: "You cannot delete yourself",
        cannotDeleteLastAdmin: "Cannot delete the last admin",

        // Validation messages
        validationError: "Validation Error",
        usernameTooShort: "Username must be at least 3 characters",
        passwordTooShort: "Password must be at least 8 characters",
        fillRequiredFields: "Please fill all required fields",
        userCreated: "User created successfully",
        passwordUpdated: "Password updated successfully",
        updateFailed: "Update Failed",

        // 403 Unauthorized page
        unauthorizedTitle: "Access Denied",
        unauthorizedSubtitle: "You don't have permission to access this page",
        unauthorizedMessage: "Please contact your administrator if you believe this is an error.",
        goBack: "Go Back",
        goHome: "Go to Dashboard"
    },
    fr: {
        // Auth
        loginTitle: "NetOps Flow",
        loginSubtitle: "Automatisation Réseau",
        username: "Nom d'utilisateur",
        password: "Mot de passe",
        signIn: "Connexion",
        accessGranted: "Accès Autorisé",
        accessDenied: "Accès Refusé",
        welcomeBack: "Bon retour.",
        authOnly: "Accès Autorisé Uniquement",

        // Sidebar
        dashboard: "Tableau de bord",
        network: "Réseau",
        ipam: "IPAM",
        topology: "Topologie",
        automation: "Automatisation",
        scriptRunner: "Exécution de Scripts",
        system: "Système",
        settings: "Paramètres",
        logout: "Déconnexion",

        // Dashboard
        totalSubnets: "Sous-réseaux",
        activeIps: "IPs Actives",
        scripts: "Scripts",
        executions: "Exécutions",
        quickActions: "Actions Rapides",
        systemStatus: "État du Système",
        dbConnected: "Base de données connectée",
        workerActive: "Worker Actif",
        newSubnet: "Nouveau Sous-réseau",
        uploadScript: "Uploader un Script",

        // IPAM
        cidr: "CIDR",
        name: "Nom",
        description: "Description",
        actions: "Actions",
        scanSubnet: "Scanner",
        addIp: "Ajouter IP",
        allocatedIps: "IPs allouées dans",
        address: "Adresse",
        hostname: "Nom d'hôte",
        mac: "Adresse MAC",
        lastScan: "Dernier Scan",
        status: "Statut",
        noIps: "Aucune IP trouvée. Cliquez sur le bouton Scan.",
        save: "Enregistrer",
        cancel: "Annuler",
        allocate: "Allouer",
        manualIpAllocation: "Allocation IP Manuelle",
        ipAddress: "Adresse IP",
        subnetCreated: "Sous-réseau Créé",
        ipAllocated: "IP Allouée",
        scanStarted: "Scan Démarré",
        addressesFound: "adresses trouvées",
        success: "Succès",
        failedCreateSubnet: "Échec création sous-réseau",
        failedAllocateIp: "Échec allocation IP",
        failedStartScan: "Échec démarrage scan",
        scanningBackground: "Scan en arrière-plan...",

        // Scripts
        uploadTitle: "Uploader un Script",
        availableScripts: "Scripts Disponibles",
        executionHistory: "Historique",
        clickDrag: "Cliquez ou glissez un fichier ici",
        targetServer: "Serveur Cible",
        localhost: "Localhost (Worker)",
        leaveEmpty: "Laisser vide pour exécution locale.",
        runNow: "Exécuter",
        enterPasswordConfirm: "Confirmez mot de passe pour exécuter",
        type: "Type",
        executionLog: "Journal d'Exécution",
        stdout: "STDOUT",
        stderr: "STDERR",
        uploaded: "Téléversé",
        error: "Erreur",
        started: "Démarré",
        scriptQueued: "Exécution du script en file d'attente",
        executionFailed: "Échec de l'exécution",
        passwordRequired: "Mot de passe requis",
        confirmPasswordDetail: "Veuillez confirmer votre mot de passe pour exécuter.",
        deleted: "Supprimé",
        scriptDeleted: "Script supprimé avec succès",
        scriptArgs: "Arguments du script",
        scriptArgsPlaceholder: "ex: --verbose -n 5",
        fileSize: "Taille du fichier",
        bytes: "octets",
        invalidFileType: "Type de fichier invalide. Seuls .py, .sh, .ps1 autorisés.",
        stop: "Arrêter",
        deleteHistory: "Effacer l'historique",
        historyDeleted: "Historique effacé",
        executionStopped: "Exécution arrêtée",
        accessDeniedTitle: "Accès Refusé",
        invalidPassword: "Mot de passe incorrect",
        invalidPasswordDetail: "Le mot de passe que vous avez entré est incorrect.",
        confirmDeleteHistory: "Êtes-vous sûr de vouloir effacer tout l'historique d'exécution ?",
        confirmDeleteScript: "Êtes-vous sûr de vouloir supprimer",

        // Settings
        myProfile: "Mon Profil",
        updatePassword: "Changer mot de passe",
        newPassword: "Nouveau mot de passe",
        userManagement: "Utilisateurs",
        serverInventory: "Inventaire Serveurs",
        newUser: "Nouvel Utilisateur",
        newServer: "Nouveau Serveur",
        role: "Rôle",
        permissions: "Permissions",
        saveUser: "Enregistrer",
        saveServer: "Enregistrer",
        viewTopo: "Voir Topologie",
        runScripts: "Lancer Scripts",
        accessSettings: "Accès Paramètres",
        accessIpam: "Accès IPAM",

        // User Management
        deleteUser: "Supprimer l'utilisateur",
        confirmDeleteUser: "Êtes-vous sûr de vouloir supprimer l'utilisateur",
        userDeleted: "Utilisateur supprimé avec succès",
        cannotDeleteSelf: "Vous ne pouvez pas vous supprimer vous-même",
        cannotDeleteLastAdmin: "Impossible de supprimer le dernier administrateur",

        // Validation messages
        validationError: "Erreur de validation",
        usernameTooShort: "Le nom d'utilisateur doit contenir au moins 3 caractères",
        passwordTooShort: "Le mot de passe doit contenir au moins 8 caractères",
        fillRequiredFields: "Veuillez remplir tous les champs obligatoires",
        userCreated: "Utilisateur créé avec succès",
        passwordUpdated: "Mot de passe mis à jour avec succès",
        updateFailed: "Échec de la mise à jour",

        // 403 Unauthorized page
        unauthorizedTitle: "Accès Refusé",
        unauthorizedSubtitle: "Vous n'avez pas la permission d'accéder à cette page",
        unauthorizedMessage: "Veuillez contacter votre administrateur si vous pensez qu'il s'agit d'une erreur.",
        goBack: "Retour",
        goHome: "Aller au tableau de bord"
    }
};

// Returns a computed ref (use .value in script, or unwrap in template)
export const t = (key) => {
    return computed(() => translations[currentLang.value][key] || key);
};

export const setLang = (lang) => {
    if (lang === 'en' || lang === 'fr') {
        currentLang.value = lang;
        localStorage.setItem('lang', lang);
    }
};

export const toggleLang = () => {
    currentLang.value = currentLang.value === 'en' ? 'fr' : 'en';
    localStorage.setItem('lang', currentLang.value);
};

export const initLang = () => {
    const saved = localStorage.getItem('lang');
    if (saved) currentLang.value = saved;
};

export const getCurrentLang = () => currentLang.value;

export const langIcon = computed(() => currentLang.value === 'en' ? '🇫🇷' : '🇺🇸');
