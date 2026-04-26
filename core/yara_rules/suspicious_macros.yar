rule Malicious_VBA_Macros {
    meta:
        description = "Detects highly suspicious VBA macro executions and Shell object invocations."
        author = "AetherGuard AI"
        date = "2026-04-20"
        threat_level = "Critical"

    strings:
        // Execution triggers
        $trigger1 = "AutoOpen" nocase wide ascii
        $trigger2 = "AutoClose" nocase wide ascii
        $trigger3 = "Document_Open" nocase wide ascii
        $trigger4 = "Workbook_Open" nocase wide ascii
        $trigger5 = "AutoExec" nocase wide ascii

        // Shell executions
        $shell1 = "Shell(" nocase wide ascii
        $shell2 = "WScript.Shell" nocase wide ascii
        $shell3 = "CreateObject(\"WScript.Shell\")" nocase wide ascii
        $shell4 = "cmd.exe /c" nocase wide ascii
        $shell5 = "powershell.exe -ExecutionPolicy Bypass" nocase wide ascii
        $shell6 = "powershell -enc" nocase wide ascii

        // Suspicious behavior
        $beh1 = "InternetXMLHTTP" nocase wide ascii
        $beh2 = "URLDownloadToFile" nocase wide ascii
        $beh3 = "SaveToFile" nocase wide ascii
        $beh4 = "Adodb.Stream" nocase wide ascii

    condition:
        // A trigger AND either a shell execution or a suspicious download behavioral pattern
        any of ($trigger*) and (any of ($shell*) or any of ($beh*))
}
