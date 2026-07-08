{
  "groups": {
    "group:hub": ["hub"],
    "group:nvr": [],
    "group:mobile": []
  },
  "acls": [
    // Hub can reach all NVRs and mobile clients
    {"action": "accept", "src": ["group:hub"], "dst": ["*:*"]},
    // NVRs can reach hub
    {"action": "accept", "src": ["group:nvr"], "dst": ["group:hub:*"]},
    // Mobile clients can reach hub and their authorized NVRs
    {"action": "accept", "src": ["group:mobile"], "dst": ["group:hub:*"]}
  ]
}
