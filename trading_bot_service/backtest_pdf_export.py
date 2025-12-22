"""
PDF Export for Backtest Results
Generates detailed trade-by-trade analysis with charts and metrics
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from datetime import datetime
import matplotlib.pyplot as plt
from io import BytesIO
import pandas as pd
import numpy as np


class BacktestPDFExporter:
    """Generate comprehensive PDF reports for backtest results"""
    
    def __init__(self, backtest_results, output_filename=None):
        """
        Initialize PDF exporter
        
        Args:
            backtest_results: Dictionary with trades, metrics
            output_filename: Output PDF filename (default: auto-generated)
        """
        self.results = backtest_results
        self.trades_df = pd.DataFrame(backtest_results.get('trades', []))
        self.filename = output_filename or f"backtest_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Section heading
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#202124'),
            spaceBefore=20,
            spaceAfter=10
        ))
        
        # Metric label
        self.styles.add(ParagraphStyle(
            name='MetricLabel',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#5f6368'),
            leftIndent=20
        ))
        
    def generate_pdf(self):
        """Generate complete PDF report"""
        # Create document
        doc = SimpleDocTemplate(
            self.filename,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Build content
        story = []
        
        # Title page
        story.extend(self._create_title_page())
        
        # Executive summary
        story.extend(self._create_executive_summary())
        story.append(PageBreak())
        
        # Equity curve chart
        story.extend(self._create_equity_curve())
        story.append(PageBreak())
        
        # Detailed trade log
        story.extend(self._create_trade_log())
        
        # Build PDF
        doc.build(story)
        print(f"✅ PDF Report generated: {self.filename}")
        return self.filename
        
    def _create_title_page(self):
        """Create title page"""
        story = []
        
        # Title
        title = Paragraph("Backtesting Report", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.3*inch))
        
        # Subtitle with strategy name
        strategy_name = self.results.get('strategy_name', 'Alpha-Ensemble Strategy')
        subtitle = Paragraph(
            f"<b>{strategy_name}</b>",
            self.styles['Heading2']
        )
        story.append(subtitle)
        story.append(Spacer(1, 0.2*inch))
        
        # Date range
        if not self.trades_df.empty:
            start_date = self.trades_df['entry_time'].min()
            end_date = self.trades_df['exit_time'].max()
            date_range = Paragraph(
                f"<b>Period:</b> {start_date} to {end_date}",
                self.styles['Normal']
            )
            story.append(date_range)
        
        story.append(Spacer(1, 0.5*inch))
        return story
        
    def _create_executive_summary(self):
        """Create executive summary with key metrics"""
        story = []
        
        # Section heading
        heading = Paragraph("Executive Summary", self.styles['SectionHeading'])
        story.append(heading)
        story.append(Spacer(1, 0.2*inch))
        
        # Calculate metrics
        initial_capital = self.results.get('initial_capital', 100000)
        final_capital = self.results.get('capital', initial_capital)
        total_return = final_capital - initial_capital
        return_pct = (total_return / initial_capital * 100) if initial_capital > 0 else 0
        
        total_trades = len(self.trades_df)
        winning_trades = len(self.trades_df[self.trades_df['pnl'] > 0]) if not self.trades_df.empty else 0
        losing_trades = len(self.trades_df[self.trades_df['pnl'] <= 0]) if not self.trades_df.empty else 0
        win_rate = self.results.get('win_rate', 0)
        profit_factor = self.results.get('profit_factor', 0)
        
        # Drawdown calculation
        if not self.trades_df.empty:
            cumulative_pnl = self.trades_df['pnl'].cumsum()
            cumulative_capital = initial_capital + cumulative_pnl
            running_max = cumulative_capital.expanding().max()
            drawdown = ((cumulative_capital - running_max) / running_max * 100).min()
        else:
            drawdown = 0
        
        # Create metrics table
        metrics_data = [
            ['Metric', 'Value'],
            ['Initial Capital', f"₹{initial_capital:,.2f}"],
            ['Final Capital', f"₹{final_capital:,.2f}"],
            ['Total Return', f"₹{total_return:,.2f} ({return_pct:.2f}%)"],
            ['Total Trades', str(total_trades)],
            ['Winning Trades', f"{winning_trades} ({win_rate:.2f}%)"],
            ['Losing Trades', str(losing_trades)],
            ['Profit Factor', f"{profit_factor:.2f}"],
            ['Max Drawdown', f"{drawdown:.2f}%"],
        ]
        
        # Add average win/loss
        if not self.trades_df.empty:
            avg_win = self.trades_df[self.trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
            avg_loss = self.trades_df[self.trades_df['pnl'] <= 0]['pnl'].mean() if losing_trades > 0 else 0
            metrics_data.append(['Avg Win', f"₹{avg_win:,.2f}"])
            metrics_data.append(['Avg Loss', f"₹{avg_loss:,.2f}"])
        
        # Create table
        metrics_table = Table(metrics_data, colWidths=[3*inch, 3*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 0.3*inch))
        
        return story
        
    def _create_equity_curve(self):
        """Create equity curve chart"""
        story = []
        
        # Section heading
        heading = Paragraph("Equity Curve", self.styles['SectionHeading'])
        story.append(heading)
        story.append(Spacer(1, 0.2*inch))
        
        if self.trades_df.empty:
            story.append(Paragraph("No trades to display", self.styles['Normal']))
            return story
        
        # Calculate cumulative P&L
        initial_capital = self.results.get('initial_capital', 100000)
        cumulative_pnl = self.trades_df['pnl'].cumsum()
        equity_curve = initial_capital + cumulative_pnl
        
        # Create plot
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(range(len(equity_curve)), equity_curve, color='#1a73e8', linewidth=2)
        ax.axhline(y=initial_capital, color='gray', linestyle='--', alpha=0.5, label='Initial Capital')
        ax.fill_between(range(len(equity_curve)), initial_capital, equity_curve, 
                        where=(equity_curve >= initial_capital), color='green', alpha=0.2)
        ax.fill_between(range(len(equity_curve)), initial_capital, equity_curve, 
                        where=(equity_curve < initial_capital), color='red', alpha=0.2)
        
        ax.set_xlabel('Trade Number', fontsize=11)
        ax.set_ylabel('Capital (₹)', fontsize=11)
        ax.set_title('Equity Curve Over Time', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Format y-axis
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))
        
        plt.tight_layout()
        
        # Save to buffer
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        # Add to story
        img = Image(img_buffer, width=6.5*inch, height=4*inch)
        story.append(img)
        story.append(Spacer(1, 0.3*inch))
        
        return story
        
    def _create_trade_log(self):
        """Create detailed trade-by-trade log"""
        story = []
        
        # Section heading
        heading = Paragraph("Detailed Trade Log", self.styles['SectionHeading'])
        story.append(heading)
        story.append(Spacer(1, 0.2*inch))
        
        if self.trades_df.empty:
            story.append(Paragraph("No trades executed", self.styles['Normal']))
            return story
        
        # Prepare trade data for table
        trade_data = [['#', 'Symbol', 'Entry Time', 'Exit Time', 'Dir', 
                      'Entry ₹', 'Exit ₹', 'P&L ₹', 'Exit']]
        
        for idx, trade in self.trades_df.iterrows():
            # Format times - extract just date and time (remove timezone/seconds)
            entry_time_str = str(trade['entry_time'])
            exit_time_str = str(trade['exit_time'])
            
            # Parse and format as "MM-DD HH:MM"
            try:
                if 'T' in entry_time_str or ' ' in entry_time_str:
                    # ISO format or space-separated
                    entry_parts = entry_time_str.replace('T', ' ').split(' ')
                    entry_date = entry_parts[0].split('-')[-2:]  # MM-DD
                    entry_time = entry_parts[1].split(':')[:2]    # HH:MM
                    entry_time = f"{'-'.join(entry_date)} {':'.join(entry_time)}"
                else:
                    entry_time = entry_time_str[:16]  # Fallback
                    
                if 'T' in exit_time_str or ' ' in exit_time_str:
                    exit_parts = exit_time_str.replace('T', ' ').split(' ')
                    exit_date = exit_parts[0].split('-')[-2:]
                    exit_time = exit_parts[1].split(':')[:2]
                    exit_time = f"{'-'.join(exit_date)} {':'.join(exit_time)}"
                else:
                    exit_time = exit_time_str[:16]  # Fallback
            except:
                entry_time = entry_time_str[:16]
                exit_time = exit_time_str[:16]
            
            # Format prices
            entry_price = f"{trade['entry_price']:.2f}"
            exit_price = f"{trade['exit_price']:.2f}"
            pnl = f"{trade['pnl']:,.2f}"
            
            # Shorten symbol name if needed
            symbol = trade['symbol'].replace('-EQ', '')
            
            # Shorten exit reason
            exit_reason = trade.get('exit_reason', 'N/A')
            if len(exit_reason) > 8:
                exit_reason = exit_reason[:8]
            
            trade_data.append([
                str(idx + 1),
                symbol,
                entry_time,
                exit_time,
                trade.get('direction', 'LONG')[:4],  # SHORT/LONG -> SHOR/LONG
                entry_price,
                exit_price,
                pnl,
                exit_reason
            ])
        
        # Create table with optimized column widths for better readability
        col_widths = [0.3*inch, 0.85*inch, 1.0*inch, 1.0*inch, 0.45*inch, 
                     0.65*inch, 0.65*inch, 0.8*inch, 0.8*inch]
        
        # Split into multiple tables if too many trades (20 per page)
        rows_per_page = 20
        for i in range(0, len(trade_data), rows_per_page):
            # Get chunk of data (include header)
            if i == 0:
                chunk = trade_data[i:i+rows_per_page]
            else:
                chunk = [trade_data[0]] + trade_data[i:i+rows_per_page]
            
            trade_table = Table(chunk, colWidths=col_widths)
            
            # Style table with proper text wrapping
            table_style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]
            
            # Color-code P&L
            for row_idx in range(1, len(chunk)):
                pnl_value = float(chunk[row_idx][7].replace(',', ''))
                if pnl_value > 0:
                    table_style.append(('TEXTCOLOR', (7, row_idx), (7, row_idx), colors.green))
                elif pnl_value < 0:
                    table_style.append(('TEXTCOLOR', (7, row_idx), (7, row_idx), colors.red))
            
            trade_table.setStyle(TableStyle(table_style))
            story.append(trade_table)
            
            # Add page break if more trades to show
            if i + rows_per_page < len(trade_data):
                story.append(PageBreak())
        
        return story


def export_backtest_to_pdf(backtest_results, output_filename=None):
    """
    Convenience function to export backtest results to PDF
    
    Args:
        backtest_results: Dictionary with trades and metrics
        output_filename: Optional output filename
        
    Returns:
        str: Path to generated PDF file
    """
    exporter = BacktestPDFExporter(backtest_results, output_filename)
    return exporter.generate_pdf()


if __name__ == "__main__":
    # Test with sample data
    sample_results = {
        'strategy_name': 'Alpha-Ensemble Strategy',
        'initial_capital': 100000,
        'capital': 115000,
        'win_rate': 65.5,
        'profit_factor': 2.1,
        'trades': [
            {
                'symbol': 'TCS',
                'entry_time': '2024-01-15 10:35:00',
                'exit_time': '2024-01-15 14:20:00',
                'direction': 'LONG',
                'entry_price': 3450.50,
                'exit_price': 3475.25,
                'quantity': 10,
                'pnl': 247.50,
                'exit_reason': 'Take Profit'
            },
            {
                'symbol': 'INFY',
                'entry_time': '2024-01-15 11:15:00',
                'exit_time': '2024-01-15 13:45:00',
                'direction': 'LONG',
                'entry_price': 1520.75,
                'exit_price': 1505.25,
                'quantity': 15,
                'pnl': -232.50,
                'exit_reason': 'Stop Loss'
            },
        ]
    }
    
    print("Testing PDF export...")
    pdf_file = export_backtest_to_pdf(sample_results, "test_backtest_report.pdf")
    print(f"✅ Test PDF created: {pdf_file}")
