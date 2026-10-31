# Public PR demonstrations

These are public pull requests that can be used for a live demonstration. The
tool reads them; it does not modify them.

- [curl #23695](https://github.com/curl/curl/pull/23695)
- [curl #23692](https://github.com/curl/curl/pull/23692)
- [curl #23690](https://github.com/curl/curl/pull/23690)

Clone the repository once, then run the queue command:

```bash
git clone https://github.com/curl/curl.git /tmp/curl
export GITHUB_TOKEN="your-read-only-token"
PYTHONPATH=src python3 -m claimlens.github_queue_cli \
  curl/curl /tmp/curl --offline \
  --output reports/curl_pr_queue.md
```

The queue will include all currently open PRs. The links above are useful for
opening individual examples during a presentation; live PR numbers and status
can change over time.
