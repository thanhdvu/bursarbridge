export const THEME_KEY = "bb-theme";

/** Runs before first paint (see InlineScript) so there is no light/dark flash. */
export const themeScript = `(function(){try{var t=localStorage.getItem("${THEME_KEY}")||"system";var d=t==="dark"||(t==="system"&&matchMedia("(prefers-color-scheme: dark)").matches);var c=document.documentElement.classList;d?c.add("dark"):c.remove("dark");document.documentElement.style.colorScheme=d?"dark":"light";}catch(e){}})();`;
