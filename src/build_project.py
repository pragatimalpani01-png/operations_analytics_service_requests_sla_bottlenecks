from pathlib import Path
import json, math, sqlite3, textwrap
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.units import mm

ROOT=Path(__file__).resolve().parents[1]
for d in ['data','analysis','outputs','visualizations','reports','sql','tests']: (ROOT/d).mkdir(exist_ok=True)
RNG=np.random.default_rng(4172026)
AS_OF=pd.Timestamp('2026-01-15 23:59:00')
N=8200
services=['Account access','Billing and payments','Delivery issue','Returns and refunds','Technical fault','Account changes','Order cancellation','Product information']
service_w=[.12,.14,.18,.15,.16,.09,.08,.08]
channels=['Email','Web form','Phone','Live chat','Internal transfer']
channel_w=[.29,.28,.19,.17,.07]
teams=['North desk','Central desk','South desk','Specialist team','Escalations']
team_w=[.23,.25,.24,.20,.08]
regions=['North','Central','South','West','East']
region_w=[.22,.20,.21,.19,.18]
priorities=['P1 - urgent','P2 - high','P3 - standard','P4 - low']
priority_w=[.06,.19,.53,.22]
created=pd.to_datetime(RNG.integers(pd.Timestamp('2025-07-01').value//10**9,pd.Timestamp('2026-01-15').value//10**9,size=N),unit='s').floor('min')
service=RNG.choice(services,N,p=service_w)
channel=RNG.choice(channels,N,p=channel_w)
team=RNG.choice(teams,N,p=team_w)
region=RNG.choice(regions,N,p=region_w)
priority=RNG.choice(priorities,N,p=priority_w)
complexity=RNG.choice(['Low','Medium','High'],N,p=[.36,.47,.17])
# Operational conditions: queues grow at a few times, rather than randomly everywhere.
dow=pd.Series(created).dt.dayofweek.to_numpy()
month=pd.Series(created).dt.month.to_numpy()
weekend=(dow>=5)
month_end=pd.Series(created).dt.is_month_end.to_numpy()
service_mult={'Account access':.78,'Billing and payments':1.08,'Delivery issue':1.26,'Returns and refunds':1.12,'Technical fault':1.55,'Account changes':.94,'Order cancellation':.82,'Product information':.68}
priority_mult={'P1 - urgent':.30,'P2 - high':.63,'P3 - standard':1.0,'P4 - low':1.50}
channel_mult={'Email':1.12,'Web form':1.03,'Phone':.80,'Live chat':.64,'Internal transfer':1.35}
team_mult={'North desk':1.02,'Central desk':1.18,'South desk':1.00,'Specialist team':1.26,'Escalations':1.48}
complex_mult={'Low':.66,'Medium':1.0,'High':1.68}
sla_map={'P1 - urgent':4,'P2 - high':8,'P3 - standard':24,'P4 - low':48}
sla=np.array([sla_map[p] for p in priority],dtype=float)
# Arrival congestion adds queue delay during Mondays and month-end; specialist work attracts handoffs.
base=np.array([RNG.lognormal(mean=2.35,sigma=.65) for _ in range(N)])
service_f=np.array([service_mult[x] for x in service]); priority_f=np.array([priority_mult[x] for x in priority]); channel_f=np.array([channel_mult[x] for x in channel]); team_f=np.array([team_mult[x] for x in team]); comp_f=np.array([complex_mult[x] for x in complexity])
handoffs=np.clip(RNG.poisson(np.array([.35 if x in ['Live chat','Phone'] else .65 for x in channel]) + np.array([.75 if x in ['Technical fault','Returns and refunds'] else .20 for x in service]) + np.array([.6 if x=='High' else 0 for x in complexity]) + np.array([.35 if x=='Specialist team' else .0 for x in team])),0,5)
queue_f=np.where(weekend,1.13,1.0)*np.where(dow==0,1.19,1.0)*np.where(month_end,1.14,1.0)
resolution_hours=base*service_f*priority_f*channel_f*team_f*comp_f*queue_f*np.exp(.23*handoffs)
resolution_hours=np.clip(resolution_hours,0.25,260)
first_response_hours=np.clip(resolution_hours*RNG.uniform(.06,.34,N)+RNG.gamma(1.2,0.6,N),0.08,48)
# Some records remain open at snapshot; long-running and complex tickets are more likely to stay open.
age_hours=(AS_OF-pd.Series(created)).dt.total_seconds().to_numpy()/3600
open_prob=np.clip(0.006 + 0.22*(age_hours<96) + 0.09*((age_hours<240)&(complexity=='High')) + 0.06*((age_hours<240)&(team=='Specialist team')) + 0.035*((age_hours<240)&(service=='Technical fault')) + 0.025*((age_hours<240)&(service=='Returns and refunds')),0,0.45)
is_open=RNG.random(N)<open_prob
# Ensure open cases are plausibly still unresolved, and resolved cases have completion times before snapshot.
actual_hours=resolution_hours.copy()
status=np.where(is_open,'Open','Resolved')
closed=pd.Series(created)+pd.to_timedelta(actual_hours,unit='h')
# Any sample that would resolve after the snapshot is open, avoiding impossible timestamps.
future=(closed>AS_OF).to_numpy()
is_open=is_open|future
status=np.where(is_open,'Open','Resolved')
closed=pd.Series(created)+pd.to_timedelta(actual_hours,unit='h')
closed_values=closed.astype('datetime64[ns]').astype('int64').to_numpy()
closed_iso=np.where(is_open,'',closed.dt.strftime('%Y-%m-%d %H:%M:%S').to_numpy())
first_response=pd.Series(created)+pd.to_timedelta(first_response_hours,unit='h')
first_response_iso=np.minimum(first_response, pd.Series(AS_OF,index=range(N))).dt.strftime('%Y-%m-%d %H:%M:%S').to_numpy()
# Open issue age is measured at snapshot, completed cycle time only for resolved records.
observed_hours=np.where(is_open,age_hours,actual_hours)
response_target=np.array([1 if p=='P1 - urgent' else 2 if p=='P2 - high' else 8 if p=='P3 - standard' else 16 for p in priority],dtype=float)
first_response_sla=first_response_hours<=response_target
resolution_sla=np.where(is_open,observed_hours<=sla,actual_hours<=sla)
reopened=np.clip(RNG.poisson(.09+np.array([.25 if x in ['Technical fault','Billing and payments'] else .07 for x in service])+np.array([.23 if x=='High' else .0 for x in complexity]),N),0,3)
csat=np.clip(np.round(4.55-.38*np.log1p(np.minimum(observed_hours,120)/8)-.27*handoffs-.22*reopened+RNG.normal(0,.6,N),1),1,5).astype(int)
# Owner groups are teams; distinct stable request IDs.
req_ids=[f'SR-{i:06d}' for i in range(1,N+1)]
df=pd.DataFrame({'request_id':req_ids,'created_at':pd.Series(created).dt.strftime('%Y-%m-%d %H:%M:%S'),'first_response_at':first_response_iso,'resolved_at':closed_iso,'status':status,'priority':priority,'service_type':service,'channel':channel,'team':team,'region':region,'complexity':complexity,'handoffs':handoffs,'reopened_count':reopened,'sla_target_hours':sla.astype(int),'first_response_target_hours':response_target.astype(int),'first_response_hours':np.round(first_response_hours,2),'resolution_hours':np.where(is_open,np.nan,np.round(actual_hours,2)),'age_at_snapshot_hours':np.round(age_hours,2),'observed_elapsed_hours':np.round(observed_hours,4),'first_response_sla_met':first_response_sla,'resolution_sla_met_or_not_yet_breached':resolution_sla,'customer_rating_1_to_5':csat,'is_weekend_arrival':weekend,'is_month_end_arrival':month_end})
df.to_csv(ROOT/'data/service_requests.csv',index=False)

# Request activity log, with realistic handling path summaries (synthetic, not an audit trail).
logs=[]
for i,row in df.iterrows():
    t=pd.Timestamp(row.created_at); hops=int(row.handoffs)
    logs.append((row.request_id,1,t.strftime('%Y-%m-%d %H:%M:%S'),'Created',row.channel,row.team, 'Request received'))
    rt=t+pd.Timedelta(hours=float(row.first_response_hours))
    logs.append((row.request_id,2,rt.strftime('%Y-%m-%d %H:%M:%S'),'First response',row.channel,row.team,'First customer-facing response'))
    for h in range(hops):
        ht=rt+pd.Timedelta(hours=float(row.observed_elapsed_hours)*(h+1)/(hops+2))
        logs.append((row.request_id,3+h,ht.strftime('%Y-%m-%d %H:%M:%S'),'Team handoff',row.channel,row.team, f'Handoff {h+1} of {hops}'))
    if row.status=='Resolved':
        logs.append((row.request_id,10,t+pd.Timedelta(hours=float(row.observed_elapsed_hours)), 'Resolved',row.channel,row.team,'Request closed'))
activity=pd.DataFrame(logs,columns=['request_id','event_sequence','event_at','event_type','intake_channel','team','event_note'])
activity['event_at']=activity['event_at'].astype(str)
activity.to_csv(ROOT/'data/request_activity_log.csv',index=False)

# Helper tables / metrics
resolved=df[df.status=='Resolved'].copy()
resolved['sla_met']=resolved['resolution_sla_met_or_not_yet_breached'].astype(bool)
# Open requests count as SLA risk only if the elapsed time has exceeded target.
df['sla_breached_or_at_risk']=~df['resolution_sla_met_or_not_yet_breached'].astype(bool)

# Summary metrics
metrics={
 'requests':int(len(df)), 'resolved':int((df.status=='Resolved').sum()), 'open':int((df.status=='Open').sum()),
 'overall_sla_met_resolved':float(resolved.resolution_sla_met_or_not_yet_breached.mean()),
 'first_response_sla_met':float(df.first_response_sla_met.mean()),
 'median_resolution_hours':float(resolved.resolution_hours.median()),
 'p90_resolution_hours':float(resolved.resolution_hours.quantile(.9)),
 'open_over_target':int(((df.status=='Open') & (df.observed_elapsed_hours>df.sla_target_hours)).sum()),
 'open_over_24h':int(((df.status=='Open') & (df.age_at_snapshot_hours>24)).sum()),
 'handoff_rate':float((df.handoffs>0).mean()), 'avg_handoffs':float(df.handoffs.mean()),
 'reopen_rate':float((df.reopened_count>0).mean()), 'csat_mean':float(df.customer_rating_1_to_5.mean())
}
with open(ROOT/'outputs/kpi_summary.json','w') as f: json.dump(metrics,f,indent=2)

# Group summaries
by_service=df.groupby('service_type').agg(requests=('request_id','count'), resolved=('status',lambda s:(s=='Resolved').sum()), median_elapsed_hours=('observed_elapsed_hours','median'), p90_elapsed_hours=('observed_elapsed_hours',lambda s:s.quantile(.9)), sla_breach_or_risk_rate=('sla_breached_or_at_risk','mean'), avg_handoffs=('handoffs','mean'), reopen_rate=('reopened_count',lambda s:(s>0).mean()), avg_rating=('customer_rating_1_to_5','mean')).reset_index().sort_values('sla_breach_or_risk_rate',ascending=False)
by_service.to_csv(ROOT/'outputs/service_type_scorecard.csv',index=False)
by_team=df.groupby('team').agg(requests=('request_id','count'), resolved=('status',lambda s:(s=='Resolved').sum()), p90_elapsed_hours=('observed_elapsed_hours',lambda s:s.quantile(.9)), sla_breach_or_risk_rate=('sla_breached_or_at_risk','mean'), avg_handoffs=('handoffs','mean'), avg_complexity_high=('complexity',lambda s:(s=='High').mean()), avg_rating=('customer_rating_1_to_5','mean')).reset_index()
by_team.to_csv(ROOT/'outputs/team_scorecard.csv',index=False)
by_channel=df.groupby('channel').agg(requests=('request_id','count'), sla_breach_or_risk_rate=('sla_breached_or_at_risk','mean'), median_elapsed_hours=('observed_elapsed_hours','median'), p90_elapsed_hours=('observed_elapsed_hours',lambda s:s.quantile(.9)), avg_handoffs=('handoffs','mean'), avg_rating=('customer_rating_1_to_5','mean')).reset_index().sort_values('requests',ascending=False)
by_channel.to_csv(ROOT/'outputs/channel_scorecard.csv',index=False)
# Month-level incoming, resolved, backlog snapshots (month-end backlog = arrival <= date and still open OR resolved later than date).
df['created_dt']=pd.to_datetime(df.created_at)
monthly=[]
created_ts=pd.to_datetime(df.created_at)
observed_end_ts=created_ts+pd.to_timedelta(df.observed_elapsed_hours,unit='h')
for period, group in df.groupby(df.created_dt.dt.to_period('M')):
    start, end=period.start_time, period.end_time
    arrivals=int(len(group))
    # Count completion events in this month, regardless of the arrival month.
    closed_this_month=int(((df.status=='Resolved') & (observed_end_ts>=start) & (observed_end_ts<=end)).sum())
    # Reconstruct what remained unfinished at each month end from arrival and completion times.
    in_backlog=int(((created_ts<=end) & ((df.status=='Open') | ((df.status=='Resolved') & (observed_end_ts>end)))).sum())
    monthly.append({'month':str(period),'arrivals':arrivals,'resolved_this_month':closed_this_month,'backlog_at_month_end':in_backlog})
monthly_df=pd.DataFrame(monthly)
monthly_df.to_csv(ROOT/'outputs/monthly_flow.csv',index=False)
# Priority risk and cohort matrix
priority_summary=df.groupby('priority').agg(requests=('request_id','count'), breach_or_risk_rate=('sla_breached_or_at_risk','mean'), median_elapsed_hours=('observed_elapsed_hours','median'), p90_elapsed_hours=('observed_elapsed_hours',lambda s:s.quantile(.9))).reset_index()
priority_summary.to_csv(ROOT/'outputs/priority_scorecard.csv',index=False)

# Queue friction score: transparent composite percentile ranks from p90/SLA, handoffs, at-risk burden.
fr=by_service.copy()
svc_sla=df.groupby('service_type').sla_target_hours.median().reset_index()
fr=fr.merge(svc_sla,on='service_type')
fr['p90_vs_sla']=fr.p90_elapsed_hours/fr.sla_target_hours
for col in ['p90_vs_sla','avg_handoffs','sla_breach_or_risk_rate']:
    fr[col+'_pct']=fr[col].rank(pct=True)
fr['queue_friction_score']=100*(.45*fr['p90_vs_sla_pct']+.30*fr['avg_handoffs_pct']+.25*fr['sla_breach_or_risk_rate_pct'])
fr=fr.sort_values('queue_friction_score',ascending=False)
fr.to_csv(ROOT/'outputs/queue_friction_score.csv',index=False)

# Workload mix adjusted team view: observed SLA-risk modeled with logistic regression-like transparent standardization.
# Weighted mean risk estimated by priority+service strata, then compare observed risk to mix expectation.
strata=df.groupby(['priority','service_type']).sla_breached_or_at_risk.mean().to_dict()
expected=[]
for _,r in df.iterrows(): expected.append(strata[(r.priority,r.service_type)])
df['expected_risk_given_mix']=expected
mix=df.groupby('team').apply(lambda g: pd.Series({'requests':len(g),'observed_risk_rate':g.sla_breached_or_at_risk.mean(),'mix_expected_risk_rate':g.expected_risk_given_mix.mean(),'risk_gap_pp':100*(g.sla_breached_or_at_risk.mean()-g.expected_risk_given_mix.mean()),'high_complexity_share':(g.complexity=='High').mean()}),include_groups=False).reset_index()
mix.to_csv(ROOT/'outputs/team_mix_adjusted_risk.csv',index=False)
# Request queue score: urgency, elapsed vs target, complexity, handoffs, reopen. Not a customer importance score.
df['elapsed_vs_sla']=df.observed_elapsed_hours/df.sla_target_hours
df['priority_base']=df.priority.map({'P1 - urgent':100,'P2 - high':75,'P3 - standard':45,'P4 - low':25})
df['queue_attention_score']=(.36*df.priority_base + .30*np.clip(df.elapsed_vs_sla*40,0,100)+.13*df.handoffs.clip(0,4)/4*100+.12*(df.complexity=='High')*100+.09*(df.reopened_count>0)*100).round(1)
# Persist useful derived fields alongside the source fields for readers who want to work in a notebook.
df.drop(columns=['created_dt'],errors='ignore').to_csv(ROOT/'data/service_requests.csv',index=False)
queue_cols=['request_id','created_at','resolved_at','status','priority','service_type','channel','team','region','complexity','handoffs','reopened_count','sla_target_hours','observed_elapsed_hours','elapsed_vs_sla','sla_breached_or_at_risk','queue_attention_score','customer_rating_1_to_5']
queue=df.sort_values('queue_attention_score',ascending=False)[queue_cols]
queue.to_csv(ROOT/'outputs/queue_attention_queue.csv',index=False)
# Compact dashboard payload
payload={'metrics':metrics,'by_service':by_service.to_dict(orient='records'),'by_team':by_team.to_dict(orient='records'),'by_channel':by_channel.to_dict(orient='records'),'monthly':monthly_df.to_dict(orient='records'),'priority':priority_summary.to_dict(orient='records'),'friction':fr.to_dict(orient='records'),'team_adjusted':mix.to_dict(orient='records'),'queue':queue.head(350).to_dict(orient='records'),'rows':df[['request_id','created_at','resolved_at','status','priority','service_type','channel','team','region','complexity','handoffs','reopened_count','sla_target_hours','observed_elapsed_hours','age_at_snapshot_hours','resolution_hours','first_response_hours','first_response_sla_met','resolution_sla_met_or_not_yet_breached','sla_breached_or_at_risk','queue_attention_score','customer_rating_1_to_5']].to_dict(orient='records'),'service_options':['All']+sorted(df.service_type.unique()),'team_options':['All']+sorted(df.team.unique()),'channel_options':['All']+sorted(df.channel.unique()),'priority_options':['All']+sorted(df.priority.unique()),'as_of':str(AS_OF.date())}
(ROOT/'outputs/dashboard_data.json').write_text(json.dumps(payload,default=lambda o: float(o) if isinstance(o,(np.floating,)) else int(o) if isinstance(o,(np.integer,)) else str(o),separators=(',',':')))

# SQLite database
con=sqlite3.connect(ROOT/'outputs/operations_analytics.db')
df.to_sql('service_requests',con,if_exists='replace',index=False)
activity.to_sql('request_activity_log',con,if_exists='replace',index=False)
con.execute('CREATE INDEX IF NOT EXISTS idx_request_created ON service_requests(created_at)')
con.execute('CREATE INDEX IF NOT EXISTS idx_request_team ON service_requests(team)')
con.commit(); con.close()

# Visualizations - business readable, clean labels.
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold'})
# 1 SLA risk vs volume
fig,ax=plt.subplots(figsize=(9,5.4)); x=by_service.requests; y=by_service.sla_breach_or_risk_rate*100
ax.scatter(x,y,s=70+by_service.avg_handoffs*65,alpha=.82)
for _,r in by_service.iterrows(): ax.annotate(r.service_type,(r.requests,r.sla_breach_or_risk_rate*100),xytext=(5,4),textcoords='offset points',fontsize=8)
ax.set_xlabel('Requests in the sample'); ax.set_ylabel('Breached or at-risk requests (%)'); ax.set_title('The biggest queue is not always the hardest queue'); ax.grid(axis='y',alpha=.25); fig.tight_layout(); fig.savefig(ROOT/'visualizations/service_volume_vs_sla_risk.png',dpi=180); plt.close(fig)
# 2 cycle time distribution log-scale
fig,ax=plt.subplots(figsize=(9,5)); data=[resolved.loc[resolved.service_type==s,'resolution_hours'].dropna().values for s in services]
ax.boxplot(data,labels=[s.replace(' and ',' & ').replace(' ','\n',1) for s in services],showfliers=False,patch_artist=True); ax.set_yscale('log'); ax.set_ylabel('Resolution time (hours, log scale)'); ax.set_title('Averages hide the long tail'); ax.grid(axis='y',alpha=.22); fig.tight_layout(); fig.savefig(ROOT/'visualizations/resolution_time_tail.png',dpi=180); plt.close(fig)
# 3 handoff tax
fig,ax=plt.subplots(figsize=(8.5,5)); hh=resolved.groupby('handoffs').resolution_hours.median().reset_index(); ax.plot(hh.handoffs,hh.resolution_hours,marker='o',linewidth=2); ax.set_xlabel('Number of handoffs'); ax.set_ylabel('Median resolution time (hours)'); ax.set_title('More handoffs tend to mean a longer wait'); ax.grid(alpha=.25); fig.tight_layout(); fig.savefig(ROOT/'visualizations/handoff_delay_curve.png',dpi=180); plt.close(fig)
# 4 monthly flow
fig,ax=plt.subplots(figsize=(8.5,5)); ax.plot(monthly_df.month,monthly_df.arrivals,marker='o',label='Arrivals'); ax.plot(monthly_df.month,monthly_df.resolved_this_month,marker='o',label='Resolved this month'); ax2=ax.twinx(); ax2.plot(monthly_df.month,monthly_df.backlog_at_month_end,marker='s',linestyle='--',label='Backlog snapshot'); ax.set_ylabel('Requests'); ax2.set_ylabel('Estimated month-end backlog'); ax.set_title('Incoming work versus work cleared'); ax.tick_params(axis='x',rotation=25); ax.grid(axis='y',alpha=.22); h,l=ax.get_legend_handles_labels(); h2,l2=ax2.get_legend_handles_labels(); ax.legend(h+h2,l+l2,loc='upper left',frameon=False); fig.tight_layout(); fig.savefig(ROOT/'visualizations/inflow_vs_clearance.png',dpi=180); plt.close(fig)
# 5 team adjusted risk
fig,ax=plt.subplots(figsize=(8.5,5)); colors_=['#B65C4B' if v>0 else '#397A78' for v in mix.risk_gap_pp]; ax.barh(mix.team,mix.risk_gap_pp,color=colors_); ax.axvline(0,color='#444',linewidth=1); ax.set_xlabel('Observed risk minus expected risk (percentage points)'); ax.set_title('A fairer team comparison: allow for the work they receive'); ax.grid(axis='x',alpha=.22); fig.tight_layout(); fig.savefig(ROOT/'visualizations/team_mix_adjusted_risk.png',dpi=180); plt.close(fig)
# 6 priority/service heatmap risk
pivot=df.pivot_table(index='service_type',columns='priority',values='sla_breached_or_at_risk',aggfunc='mean').reindex(services)
fig,ax=plt.subplots(figsize=(9,5.5)); im=ax.imshow(pivot.values,aspect='auto',vmin=0,vmax=1,cmap='YlOrRd'); ax.set_xticks(range(len(pivot.columns)),labels=pivot.columns,rotation=20,ha='right'); ax.set_yticks(range(len(pivot.index)),labels=pivot.index); ax.set_title('Where SLA risk concentrates: request type and priority'); cb=fig.colorbar(im,ax=ax); cb.set_label('Share breached or at risk');
for i in range(len(pivot.index)):
    for j in range(len(pivot.columns)):
        v=pivot.iloc[i,j]
        if not np.isnan(v): ax.text(j,i,f'{v:.0%}',ha='center',va='center',fontsize=8,color='black' if v<.65 else 'white')
fig.tight_layout(); fig.savefig(ROOT/'visualizations/sla_risk_heatmap.png',dpi=180); plt.close(fig)
# 7 attention score histogram
fig,ax=plt.subplots(figsize=(8.5,5)); ax.hist(df.queue_attention_score,bins=25,edgecolor='white'); ax.set_xlabel('Queue attention score (0-100)'); ax.set_ylabel('Requests'); ax.set_title('A queue is easier to manage when urgency is visible'); ax.grid(axis='y',alpha=.2); fig.tight_layout(); fig.savefig(ROOT/'visualizations/queue_attention_score.png',dpi=180); plt.close(fig)

# Report with generated findings and recommendations
worst=fr.iloc[0]; best_team=mix.sort_values('risk_gap_pp').iloc[0]; worst_team=mix.sort_values('risk_gap_pp').iloc[-1]
svc_late=by_service.sort_values('sla_breach_or_risk_rate',ascending=False).iloc[0]
waits=resolved.groupby('handoffs').resolution_hours.median()
h0=float(waits.get(0,np.nan)); h1=float(waits.get(1,np.nan)); h2=float(waits.get(2,np.nan))
styles=getSampleStyleSheet(); styles.add(ParagraphStyle(name='ReportTitle',parent=styles['Title'],fontName='Helvetica-Bold',fontSize=24,leading=28,textColor=colors.HexColor('#173A46'),spaceAfter=8)); styles.add(ParagraphStyle(name='Deck',parent=styles['Normal'],fontSize=11,leading=16,textColor=colors.HexColor('#52656B'),spaceAfter=14)); styles.add(ParagraphStyle(name='H1x',parent=styles['Heading1'],fontSize=15,leading=19,textColor=colors.HexColor('#173A46'),spaceBefore=8,spaceAfter=7)); styles.add(ParagraphStyle(name='Bodyx',parent=styles['BodyText'],fontSize=9.3,leading=13.2,spaceAfter=7)); styles.add(ParagraphStyle(name='Smallx',parent=styles['BodyText'],fontSize=7.5,leading=10,textColor=colors.HexColor('#57666B'),spaceAfter=4))
report=ROOT/'reports/operations_analytics_review.pdf'
story=[]
story += [Spacer(1,12*mm),Paragraph('Operations Analytics',styles['ReportTitle']),Paragraph('Service requests, SLA pressure and the delays hiding between teams',styles['Deck']),Paragraph(f'Decision brief | Sample period July 2025 to mid-January 2026 | Snapshot date {AS_OF.date()}',styles['Smallx']),Spacer(1,8*mm)]
# KPI table
kdata=[['Requests','Resolved','Still open','SLA met','Median (h)','P90 (h)'],[f"{metrics['requests']:,}",f"{metrics['resolved']:,}",f"{metrics['open']:,}",f"{metrics['overall_sla_met_resolved']:.1%}",f"{metrics['median_resolution_hours']:.1f} h",f"{metrics['p90_resolution_hours']:.1f} h"]]
t=Table(kdata,colWidths=[27*mm]*6); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#173A46')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTNAME',(0,1),(-1,-1),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8),('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('BACKGROUND',(0,1),(-1,1),colors.HexColor('#EEF3F2')),('BOX',(0,0),(-1,-1),.4,colors.HexColor('#CDD7D7')),('INNERGRID',(0,0),(-1,-1),.3,colors.HexColor('#CDD7D7')),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)])); story += [t,Spacer(1,7*mm)]
story += [Paragraph('What the numbers are saying',styles['H1x']),Paragraph(f"There are {metrics['requests']:,} requests in this sample, of which {metrics['open']:,} are still open at the snapshot date. Among resolved requests, {metrics['overall_sla_met_resolved']:.1%} finished within their target. The median resolution time is {metrics['median_resolution_hours']:.1f} hours, but the 90th percentile is {metrics['p90_resolution_hours']:.1f} hours. That gap is the operational story: the typical ticket and the ticket customers remember are often not the same ticket.",styles['Bodyx']),Paragraph(f"{int(metrics['open_over_target']):,} open requests have already used more than their resolution target. That is a more actionable watchlist than a single backlog count, because it separates unfinished work that is still within its promise from work that has already crossed it.",styles['Bodyx']),Spacer(1,3*mm),Paragraph('Read the shape of the queue',styles['H1x']),Image(str(ROOT/'visualizations/service_volume_vs_sla_risk.png'),width=165*mm,height=99*mm),Paragraph('This view puts volume beside the share of requests that have breached or are at risk of breaching their target. Bubble size indicates average handoffs. The work to tackle first is not automatically the biggest category; look for queues that combine meaningful volume, high risk and repeated movement between teams.',styles['Smallx']),PageBreak()]
story += [Paragraph('The long tail is the service problem',styles['H1x']),Image(str(ROOT/'visualizations/resolution_time_tail.png'),width=165*mm,height=97*mm),Paragraph('A median can look comfortable while a smaller group waits much longer. The report uses the 90th percentile alongside the median to avoid treating the majority experience as the whole story. The chart uses a log scale because request times range from short contacts to multi-day cases.',styles['Bodyx']),Image(str(ROOT/'visualizations/handoff_delay_curve.png'),width=160*mm,height=88*mm),Paragraph(f"In the sample, the median among resolved cases with zero handoffs is {h0:.1f} hours, compared with {h1:.1f} hours for one handoff and {h2:.1f} hours for two. This is an association, not proof that a handoff causes that entire delay: harder cases are more likely to be handed off. It is still a strong reason to inspect repeat handoffs and ownership changes on long-running requests.",styles['Bodyx']),PageBreak()]
story += [Paragraph('Where pressure is building',styles['H1x']),Image(str(ROOT/'visualizations/inflow_vs_clearance.png'),width=165*mm,height=96*mm),Paragraph('The monthly view compares incoming volume with work cleared and a reconstructed month-end backlog. The backlog measure is estimated from each request’s arrival and elapsed time. It is useful for spotting pressure, but it is not a substitute for an actual daily queue snapshot or a capacity plan.',styles['Bodyx']),Image(str(ROOT/'visualizations/sla_risk_heatmap.png'),width=165*mm,height=100*mm),Paragraph('The heatmap helps separate service types where a stricter priority target may be doing its job from service types where work routinely outlasts its promise. Read low-volume cells cautiously; the same percentage can represent very different numbers of requests.',styles['Bodyx']),PageBreak()]
story += [Paragraph('Compare teams without rewarding easy work',styles['H1x']),Image(str(ROOT/'visualizations/team_mix_adjusted_risk.png'),width=165*mm,height=95*mm),Paragraph(f"The team view adjusts each team’s observed risk for the priority and service-type mix it received. {best_team.team} has the lowest risk gap in this synthetic sample, while {worst_team.team} has the highest. This is a lightweight case-mix adjustment, not a staff performance rating. It does not account for every factor, such as staffing levels, skill mix, shift coverage or live queue size.",styles['Bodyx']),Paragraph('The queue friction score',styles['H1x']),Paragraph(f"The highest-friction service type in this run is {worst.service_type}, scoring {worst.queue_friction_score:.0f} out of 100. The score blends percentile ranks for p90 elapsed time relative to target, average handoffs and the share breached or at risk. It is intentionally transparent: the score points managers toward queues to inspect; it does not replace operational judgement.",styles['Bodyx']),Image(str(ROOT/'visualizations/queue_attention_score.png'),width=150*mm,height=86*mm),PageBreak()]
story += [Paragraph('What to change first',styles['H1x']),Paragraph('<b>1. Create an aged-work review, not just a backlog review.</b> Start each shift with open requests that have consumed most or all of their target. Assign an owner and a next action, not only a new status.',styles['Bodyx']),Paragraph('<b>2. Find the repeat handoff.</b> Review the longest-running tickets with two or more handoffs. Look for missing intake information, unclear ownership, specialist queues that need a simpler decision tree, or transfers that could have been avoided.',styles['Bodyx']),Paragraph('<b>3. Set queue-specific working rules.</b> Start with the highest-friction service types and the priority cells with the highest late share. Use an explicit escalation threshold and make the threshold visible to the team.',styles['Bodyx']),Paragraph('<b>4. Compare teams on like-for-like work.</b> Keep the mix-adjusted view as a prompt for investigation. Add staffing, shift hours and incoming volume before using it to discuss team performance.',styles['Bodyx']),Paragraph('<b>5. Run a small change before changing the whole operation.</b> Pick one queue, reduce avoidable transfers or add a clear first-touch checklist, and compare its p90 time and SLA result against a similar queue over the same period. Record what else changed.',styles['Bodyx']),Spacer(1,4*mm),Paragraph('Method and cautions',styles['H1x']),Paragraph('All records in this repository are synthetic and were generated for portfolio demonstration. SLA targets are illustrative service rules attached to each priority, not an external standard. Open cases are counted as at risk when their elapsed age is greater than the target; resolved SLA performance is calculated separately. Team mix adjustment uses service type and priority strata only. The queue attention score is a triage aid, not a measure of customer value or staff quality. The generated activity file is a plausible event path rather than an audited history. No real customer, team or company data is included.',styles['Bodyx']),Paragraph('Reproduce the analysis with <font name="Courier">python src/build_project.py</font> after installing requirements, or use the project’s <font name="Courier">run_analysis.py</font> entry point. Outputs include CSV scorecards, a SQLite database, the dashboard data payload and figures used in this brief.',styles['Smallx'])]
def footer(canvas,doc):
    canvas.saveState(); canvas.setStrokeColor(colors.HexColor('#CFD9D8')); canvas.line(18*mm,14*mm,192*mm,14*mm); canvas.setFont('Helvetica',7); canvas.setFillColor(colors.HexColor('#657377')); canvas.drawString(18*mm,9*mm,'Operations Analytics | Synthetic portfolio project'); canvas.drawRightString(192*mm,9*mm,f'Page {doc.page}'); canvas.restoreState()
doc=SimpleDocTemplate(str(report),pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=17*mm,bottomMargin=20*mm,title='Operations Analytics: Service Requests, SLA Proxies and Bottlenecks',author='Portfolio Project')
doc.build(story,onFirstPage=footer,onLaterPages=footer)

print(json.dumps({'root':str(ROOT),'metrics':metrics,'top_friction':fr[['service_type','queue_friction_score','sla_breach_or_risk_rate','p90_elapsed_hours']].head(3).to_dict('records'),'team_adjusted':mix.to_dict('records'),'files':len(list(ROOT.rglob('*')))},indent=2))
