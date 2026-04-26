rule Embedded_Executable {
    meta:
        description = "Detects MZ (DOS Executable) headers embedded significantly deep inside a file, implying steganography or payload embedding."
        author = "AetherGuard AI"
        date = "2026-04-20"
        threat_level = "High"

    strings:
        $mz_header = "MZ" 

    condition:
        // The MZ header exists, but it is NOT at the absolute very beginning of the file (offset 0). 
        // This implies an executable was pasted into the middle of another file type.
        $mz_header in (100..filesize)
}

rule Suspicious_Botnet_Strings {
    meta:
        description = "Detects common strings associated with botnets and reverse shells."
        author = "AetherGuard AI"
        date = "2026-04-20"
        threat_level = "Critical"

    strings:
        $s1 = "socket.socket(socket.AF_INET, socket.SOCK_STREAM)" nocase wide ascii
        $s2 = "/bin/sh -i" nocase wide ascii
        $s3 = "nc -e /bin/sh" nocase wide ascii
        $s4 = "Invoke-Expression" nocase wide ascii
        $s5 = "IEX (New-Object Net.WebClient).DownloadString" nocase wide ascii

    condition:
        any of ($s*)
}
