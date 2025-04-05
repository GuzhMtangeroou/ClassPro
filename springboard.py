from CPBlock import*
import sys

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmdvalue = sys.argv[1]
    else:
        cmdvalue = None
    
    if cmdvalue == None:
        sys.exit(0)
    if cmdvalue == "qs":
        qs.run_quickstart()
    if cmdvalue == "testmode":
        testmode.run()
    if cmdvalue == "mdwidget":
        MarkdownWidgetManager.run_markdown_widget_manager()
    if cmdvalue == "htmlwidget":
        HtmlWidgetManager.run_html_widget_manager()