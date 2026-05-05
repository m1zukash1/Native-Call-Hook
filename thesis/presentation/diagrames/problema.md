```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'fontSize': '22px',
    'fontFamily': 'Arial, sans-serif',
    'primaryColor': '#dbeafe',
    'primaryTextColor': '#1e3a5f',
    'primaryBorderColor': '#3b82f6',
    'lineColor': '#4b5563',
    'secondaryColor': '#dcfce7',
    'tertiaryColor': '#fef9c3'
  }
}}%%
flowchart TD
    App("📱 Android App\nJava / Kotlin")

    SLL("System.loadLibrary\n'liba'")
    LibA("liba.so")
    DLO("dlopen\n'liblibb.so'")
    Linker("⚙️ Bionic Dynamic Linker")
    LibBenc("🔒 liblibb.so\nUžšifruota diske")
    Fail("❌ Bad ELF magic")

    JavaHook("🪝 Java Hook\nXposed / LSPosed"),kf5r

    App --> SLL
    SLL --> LibA
    LibA --> DLO
    DLO --> Linker
    Linker --> LibBenc
    LibBenc --> Fail

    SLL -. "✅ Mato" .-> JavaHook
    DLO -. "❌ Nemato" .-> JavaHook

    style App fill:#dbeafe,stroke:#3b82f6,color:#1e3a5f
    style SLL fill:#dbeafe,stroke:#3b82f6,color:#1e3a5f
    style LibA fill:#dbeafe,stroke:#3b82f6,color:#1e3a5f
    style DLO fill:#fef9c3,stroke:#ca8a04,color:#713f12
    style Linker fill:#f3f4f6,stroke:#6b7280,color:#111827
    style LibBenc fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    style Fail fill:#dc2626,stroke:#991b1b,color:#ffffff
    style JavaHook fill:#fef3c7,stroke:#d97706,color:#78350f
```
