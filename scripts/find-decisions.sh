#!/usr/bin/env zsh
# find-decisions.sh - Search for decision documents in the project
# Usage: ./scripts/find-decisions.sh [all|architecture|technical|product|process|approved|proposed|deprecated]

set -e

DOCS_DIR="docs"
COMMAND="${1:-all}"

echo "🔍 Searching for decision documents..."
echo ""

case "$COMMAND" in
  all)
    echo "📋 All Decision Documents:"
    echo ""
    echo "Decision files (decision-*.md):"
    find "$DOCS_DIR" -type f -name "decision-*.md" 2>/dev/null | sort || echo "  (none found)"
    echo ""
    echo "Architecture Decision Records (ADRs):"
    find "$DOCS_DIR/development/architecture/adrs" -type f -name "*.md" 2>/dev/null | sort || echo "  (none found)"
    ;;

  architecture|technical|product|process)
    echo "📋 Decision Documents - Category: $COMMAND"
    echo ""
    find "$DOCS_DIR" -type f -name "decision-*.md" -o -path "*/adrs/*.md" 2>/dev/null | \
      xargs grep -l "category: $COMMAND" 2>/dev/null | sort || echo "  (none found)"
    ;;

  approved|proposed|deprecated)
    echo "📋 Decision Documents - Status: $COMMAND"
    echo ""
    find "$DOCS_DIR" -type f -name "decision-*.md" -o -path "*/adrs/*.md" 2>/dev/null | \
      xargs grep -l "status: $COMMAND" 2>/dev/null | sort || echo "  (none found)"
    ;;

  *)
    echo "❌ Unknown command: $COMMAND"
    echo ""
    echo "Usage: $0 [all|architecture|technical|product|process|approved|proposed|deprecated]"
    echo ""
    echo "Examples:"
    echo "  $0 all                 # List all decision documents"
    echo "  $0 architecture        # List architecture decisions"
    echo "  $0 approved            # List approved decisions"
    exit 1
    ;;
esac

echo ""
echo "✅ Search complete"
