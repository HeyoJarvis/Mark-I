import React from 'react'

type DashboardData = {
	businessName: string;
	track: Track;
	completedAt: string;
	totalFields: number;
	paymentTotal: number;
}

type Props = { 
	isOpen: boolean; 
	onClose: () => void; 
	inline?: boolean;
	onDashboardComplete?: (dashboardData: DashboardData) => void;
}

type Field = { id: string; label: string; placeholder?: string; type?: 'text'|'email'|'number'|'date' }

type Track = 'with-space' | 'no-space'

type WorkflowStep = 'setup' | 'data-intake' | 'handoff' | 'payment' | 'dashboard'

export default function WorkflowForm({ isOpen, onClose, inline = false, onDashboardComplete }: Props) {
	const [currentStep, setCurrentStep] = React.useState<WorkflowStep>('setup')
	const [formStep, setFormStep] = React.useState<1|2>(1)
	const [track, setTrack] = React.useState<Track>('with-space')
	const [values, setValues] = React.useState<Record<string,string>>({})
	const [paymentData, setPaymentData] = React.useState({
		cardNumber: '',
		expiry: '',
		cvc: '',
		expedited: false
	})
	const [assistantMessages, setAssistantMessages] = React.useState<{ from: 'assistant' | 'user'; text: string }[]>([
		{ from: 'assistant', text: 'Hi! I\'m your legal assistant. I can help answer questions about business formation, compliance requirements, and legal processes. What would you like to know?' }
	])
	const [assistantInput, setAssistantInput] = React.useState('')
	const [showAssistantChat, setShowAssistantChat] = React.useState(false)
	

	React.useEffect(() => {
		if (isOpen) { 
			// Start at setup step (physical location choice)
			setCurrentStep('setup')
			setFormStep(1)
			// Clear form data when restarting demo flow
			setValues({})
			setPaymentData({
				cardNumber: '',
				expiry: '',
				cvc: '',
				expedited: false
			})
			// Reset legal assistant chat
			setAssistantMessages([
				{ from: 'assistant', text: 'Hi! I\'m your legal assistant. I can help answer questions about business formation, compliance requirements, and legal processes. What would you like to know?' }
			])
			setAssistantInput('')
			setShowAssistantChat(false)
			
		}
	}, [isOpen])

	if (!isOpen) return null

	type FieldGroup = { title: string; fields: Field[] }

	// Track 2 — Physical Space Secured (detailed)
	const withSpaceGroups: FieldGroup[] = [
		{ title: 'Business Identity', fields: [
			{ id:'legalBusinessName', label:'Legal business name' },
			{ id:'dba', label:'DBA / trade name (if any)' },
			{ id:'entityType', label:'Entity type (LLC, C‑Corp, S‑Corp intent)' },
			{ id:'stateOfFormation', label:'State of formation' },
			{ id:'principalAddress', label:'Principal business address (physical location)' },
			{ id:'mailingAddress', label:'Mailing address (if different)' },
			{ id:'businessDescription', label:'Business description / NAICS code' },
			{ id:'businessStartDate', label:'Business start date', type:'date' },
			{ id:'effectiveFilingDate', label:'Effective filing date (optional)', type:'date' },
			{ id:'contactName', label:'Contact of record (name)' },
			{ id:'contactEmail', label:'Contact email', type:'email' },
			{ id:'contactPhone', label:'Contact phone' },
		] },
		{ title: 'Local business license', fields: [
			{ id:'lblCityCounty', label:'Jurisdiction city & county' },
			{ id:'lblHours', label:'Hours of operation' },
			{ id:'lblEmployeeCount', label:'Employee count at opening' },
			{ id:'lblEmergencyContact', label:'Emergency contact info' },
		] },
		{ title: 'Health department permit', fields: [
			{ id:'hdMenu', label:'Menu (draft)' },
			{ id:'hdFloorPlan', label:'Floor plan file' },
			{ id:'hdEquipmentList', label:'Equipment list' },
			{ id:'hdWater', label:'Water supply type (municipal / well)' },
			{ id:'hdSewage', label:'Sewage disposal (municipal / septic)' },
			{ id:'hdGreaseTrap', label:'Grease trap details' },
			{ id:'hdWasteHauler', label:'Waste hauler company' },
			{ id:'hdFoodManager', label:'Food manager certificate holder info' },
		] },
		{ title: 'Food handler certification', fields: [
			{ id:'fhName', label:'Candidate name' },
			{ id:'fhDob', label:'DOB', type:'date' },
			{ id:'fhEmail', label:'Email', type:'email' },
		] },
		{ title: 'Signage permit', fields: [
			{ id:'sgType', label:'Sign type' },
			{ id:'sgDimensions', label:'Dimensions' },
			{ id:'sgIllumination', label:'Illumination type' },
			{ id:'sgFacadePhoto', label:'Facade photo file' },
			{ id:'sgLandlordApproval', label:'Landlord approval file' },
			{ id:'sgInstaller', label:'Installer company info' },
			{ id:'sgSitePlan', label:'Site plan file' },
		] },
		{ title: 'Compliance & Insurance', fields: [
			{ id:'dorInfo', label:'Sales tax registration (state DOR info)' },
			{ id:'glSqft', label:'General liability: premises sq. ft.' },
			{ id:'glSprinkler', label:'Sprinklered? (yes/no)' },
			{ id:'glRevenue', label:'Estimated annual revenue' },
			{ id:'glClaims', label:'Prior claims? (yes/no)' },
			{ id:'wcPayroll', label:'Workers\' comp: payroll estimate' },
			{ id:'wcClassCodes', label:'Workers\' comp: class codes' },
			{ id:'wcPriorCoverage', label:'Workers\' comp: prior coverage? (yes/no)' },
		] },
		{ title: 'Uploads / Evidence Vault', fields: [
			{ id:'uploadEinLetter', label:'CP‑575 EIN letter (after issued)' },
			{ id:'uploadStateFormation', label:'State formation certificate (after issued)' },
			{ id:'uploadResaleCert', label:'Resale certificate (if applied)' },
			{ id:'uploadLease', label:'Lease agreement file' },
			{ id:'uploadProofInsurance', label:'Proof of insurance file' },
			{ id:'uploadFoodManagerCert', label:'Food manager cert file' },
			{ id:'uploadFloorPlan', label:'Floor plan file' },
		] },
	]

	// Track 1 — No physical space yet (idea stage)
	const noSpaceGroups: FieldGroup[] = [
		{ title: 'Business Identity', fields: [
			{ id:'legalBusinessName', label:'Legal business name' },
			{ id:'dba', label:'DBA / trade name (if any)' },
			{ id:'entityType', label:'Entity type (LLC, C‑Corp, S‑Corp intent)' },
			{ id:'stateOfFormation', label:'State of formation' },
			{ id:'principalAddress', label:'Principal mailing address' },
			{ id:'businessDescription', label:'Business description / NAICS code' },
			{ id:'businessStartDate', label:'Business start date (planned)', type:'date' },
			{ id:'effectiveFilingDate', label:'Effective filing date (optional)', type:'date' },
			{ id:'contactName', label:'Contact of record (name)' },
			{ id:'contactEmail', label:'Contact email', type:'email' },
			{ id:'contactPhone', label:'Contact phone' },
		] },
		{ title: 'Ownership & Governance', fields: [
			{ id:'owners', label:'Owners / members / shareholders (names, addresses, % ownership, contributions)' },
			{ id:'managementStructure', label:'Management structure (member‑managed / manager‑managed / board)' },
			{ id:'authorizedRep', label:'Authorized representative / incorporator (signer)' },
			{ id:'corpShares', label:'Authorized shares (for corporations)' },
			{ id:'parValue', label:'Par value (for corporations)' },
			{ id:'shareClasses', label:'Share classes (for corporations)' },
		] },
		{ title: 'IRS / Federal', fields: [
			{ id:'responsibleParty', label:'Responsible party (name, SSN/ITIN/EIN, title, address, contact)' },
			{ id:'einReason', label:'Reason for EIN' },
			{ id:'expectedEmployees', label:'Expected employees in next 12 months (#, categories)' },
			{ id:'accountingYearEnd', label:'Accounting year end month' },
			{ id:'sCorpElection', label:'S‑Corp election flag' },
		] },
		{ title: 'Early‑Stage Optional', fields: [
			{ id:'resaleCertInfo', label:'Resale certificate application info' },
			{ id:'foodHandlerCandidates', label:'Food handler certification candidate info' },
		] },
		{ title: 'Uploads / Evidence Vault', fields: [
			{ id:'uploadEinLetter', label:'CP‑575 EIN letter (after issued)' },
			{ id:'uploadStateFormation', label:'State formation certificate (after issued)' },
			{ id:'uploadResaleCert', label:'Resale certificate (if applied)' },
		] },
	]

	const groups: FieldGroup[] = track === 'no-space' ? noSpaceGroups : withSpaceGroups

	const handleDashboardClose = () => {
		// Create dashboard data to pass back to chat
		const dashboardData: DashboardData = {
			businessName: values.legalBusinessName || 'Your Business',
			track: track,
			completedAt: new Date().toISOString(),
			totalFields: Object.keys(values).length,
			paymentTotal: 224 + (paymentData.expedited ? 50 : 0)
		}
		
		// Call the completion handler if provided
		if (onDashboardComplete) {
			onDashboardComplete(dashboardData)
		}
		
		// Close the form
		onClose()
	}

	const sendAssistantMessage = () => {
		const v = assistantInput.trim()
		if (!v) return
		
		setAssistantMessages(m => [...m, { from: 'user', text: v }])
		setAssistantInput('')
		
		// Simple responses for demo
		setTimeout(() => {
			let response = "I understand your question. Let me help you with that."
			
			if (v.toLowerCase().includes('llc')) {
				response = "An LLC (Limited Liability Company) provides personal asset protection and tax flexibility. It's often the best choice for small businesses. The formation process typically takes 1-2 weeks and costs vary by state."
			} else if (v.toLowerCase().includes('ein')) {
				response = "An EIN (Employer Identification Number) is required for most businesses. You can apply directly with the IRS online for free, or I can handle it as part of your business formation package."
			} else if (v.toLowerCase().includes('permit') || v.toLowerCase().includes('license')) {
				response = "Business permits and licenses vary by industry and location. For a coffee shop, you'll typically need a business license, food service permit, and possibly signage permits. I can help identify all requirements for your specific situation."
			} else if (v.toLowerCase().includes('tax')) {
				response = "Business tax obligations depend on your entity type and location. LLCs have pass-through taxation by default, but can elect corporate taxation. I recommend consulting with a tax professional for your specific situation."
			} else if (v.toLowerCase().includes('upload') || v.toLowerCase().includes('document')) {
				response = "For document uploads, make sure you have clear, legible copies. The EIN letter typically arrives 2-4 weeks after filing, and state certificates can take 1-3 weeks depending on your state's processing time."
			} else if (v.toLowerCase().includes('operating agreement')) {
				response = "An Operating Agreement defines how your LLC will be managed, member responsibilities, and profit distribution. While not required in all states, it's highly recommended to protect your business and clarify operations."
			}
			
			setAssistantMessages(m => [...m, { from: 'assistant', text: response }])
		}, 1000)
	}


	const steps = [
		{ id: 'setup', label: 'Workflow Setup', active: currentStep === 'setup' },
		{ id: 'data-intake', label: 'Data Intake', active: currentStep === 'data-intake' },
		{ id: 'handoff', label: 'Handoff to Rocket Lawyer', active: currentStep === 'handoff' },
		{ id: 'payment', label: 'Payment', active: currentStep === 'payment' },
		{ id: 'dashboard', label: 'Compliance Dashboard', active: currentStep === 'dashboard' },
	]

	const getStepIndex = (step: WorkflowStep) => steps.findIndex(s => s.id === step)
	const currentStepIndex = getStepIndex(currentStep)

	const ProgressBar = () => (
		<div className="mb-12">
			<div className="flex items-center justify-between relative">
				{/* Progress line */}
				<div className="absolute top-4 left-0 right-0 h-0.5 bg-gradient-to-r from-gray-200 via-gray-200 to-gray-200">
					<div 
						className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 transition-all duration-700 ease-out rounded-full"
						style={{ width: `${(currentStepIndex / (steps.length - 1)) * 100}%` }}
					/>
				</div>

				{steps.map((step, index) => (
					<div key={step.id} className="relative flex flex-col items-center z-10">
						<div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-all duration-500 ${
							index <= currentStepIndex 
								? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-200' 
								: 'bg-white border-2 border-gray-300 text-gray-400'
						}`}>
							{index < currentStepIndex ? (
								<svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
									<path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
								</svg>
							) : (
								index + 1
							)}
						</div>
						<div className={`mt-3 text-xs font-medium text-center max-w-24 leading-tight transition-colors duration-300 ${
							index <= currentStepIndex ? 'text-indigo-700' : 'text-gray-500'
						}`}>
							{step.label}
						</div>
					</div>
				))}
			</div>
		</div>
	)

	const renderSetupStep = () => (
		<div className="max-w-7xl mx-auto">
			{formStep === 1 && (
				<div className="bg-white rounded-3xl border border-gray-100 shadow-xl shadow-gray-100/50 overflow-hidden">
					<div className="bg-gradient-to-r from-indigo-50 via-white to-purple-50 p-8 border-b border-gray-100">
						<div className="text-center">
							<h2 className="text-2xl font-bold text-gray-900 mb-3">Business Location Assessment</h2>
							<p className="text-gray-600 max-w-lg mx-auto">
								This determines which compliance track we'll follow and ensures we gather the right information for your specific situation
							</p>
						</div>
					</div>
					
					<div className="p-10">
						<div className="grid md:grid-cols-2 gap-6 max-w-2xl mx-auto">
							<button 
								className={`group relative p-8 rounded-2xl border-2 transition-all duration-300 ${
									track === 'with-space'
										? 'border-indigo-200 bg-gradient-to-br from-indigo-50 to-purple-50 shadow-lg shadow-indigo-100/50'
										: 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-md'
								}`} 
								onClick={() => setTrack('with-space')}
							>
								<div className="text-center">
									<div className={`inline-flex items-center justify-center w-12 h-12 rounded-xl mb-4 transition-colors ${
										track === 'with-space' 
											? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white' 
											: 'bg-gray-100 text-gray-500 group-hover:bg-gray-200'
									}`}>
										<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H3m2 0h3M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
										</svg>
									</div>
									<h3 className="text-lg font-semibold text-gray-900 mb-2">Yes, I have a space</h3>
									<p className="text-sm text-gray-600 leading-relaxed">
										Physical location secured with permits, licenses, and local compliance requirements
									</p>
								</div>
								{track === 'with-space' && (
									<div className="absolute top-4 right-4">
										<div className="w-6 h-6 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center">
											<svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
												<path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
											</svg>
										</div>
									</div>
								)}
							</button>
							
							<button 
								className={`group relative p-8 rounded-2xl border-2 transition-all duration-300 ${
									track === 'no-space'
										? 'border-indigo-200 bg-gradient-to-br from-indigo-50 to-purple-50 shadow-lg shadow-indigo-100/50'
										: 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-md'
								}`} 
								onClick={() => setTrack('no-space')}
							>
								<div className="text-center">
									<div className={`inline-flex items-center justify-center w-12 h-12 rounded-xl mb-4 transition-colors ${
										track === 'no-space' 
											? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white' 
											: 'bg-gray-100 text-gray-500 group-hover:bg-gray-200'
									}`}>
										<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
										</svg>
									</div>
									<h3 className="text-lg font-semibold text-gray-900 mb-2">No, still planning</h3>
									<p className="text-sm text-gray-600 leading-relaxed">
										Early-stage planning with foundational business structure and federal requirements
									</p>
								</div>
								{track === 'no-space' && (
									<div className="absolute top-4 right-4">
										<div className="w-6 h-6 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center">
											<svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
												<path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
											</svg>
										</div>
									</div>
								)}
							</button>
						</div>

						<div className="text-center mt-10">
							<button 
								className="group inline-flex items-center px-8 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold rounded-2xl hover:from-indigo-700 hover:to-purple-700 transition-all duration-300 shadow-lg shadow-indigo-200/50 hover:shadow-xl hover:shadow-indigo-300/50"
								onClick={() => setFormStep(2)}
							>
								Continue Setup
								<svg className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
								</svg>
							</button>
						</div>
						</div>
					</div>
				)}

			{formStep === 2 && (
				<div className="bg-white rounded-3xl border border-gray-100 shadow-xl shadow-gray-100/50 overflow-hidden">
					<div className="bg-gradient-to-r from-indigo-50 via-white to-purple-50 p-8 border-b border-gray-100">
						<div className="flex items-center justify-between">
					<div>
								<h2 className="text-2xl font-bold text-gray-900 mb-2">Essential Business Information</h2>
								<p className="text-gray-600">Foundation details for your business registration and compliance</p>
							</div>
							<div className="flex items-center space-x-3">
								<div className="px-4 py-2 bg-white rounded-full border border-gray-200 shadow-sm">
									<span className="text-sm font-medium text-gray-700">
										{track === 'with-space' ? 'Physical Space Track' : 'Pre-lease Planning Track'}
									</span>
								</div>
								<div className="w-3 h-3 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full"></div>
							</div>
						</div>
										</div>
					
					<div className="p-8">
						{groups.slice(0, 1).map(g => (
							<div key={g.title} className="mb-8">
								<div className="mb-8">
									<h3 className="text-xl font-bold text-gray-900 mb-2">{g.title}</h3>
									<p className="text-gray-600">Core information required for business formation and legal compliance</p>
								</div>
								
								<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6">
									{g.fields.map(f => (
										<div key={f.id} className="group">
											<label className="block text-sm font-semibold text-gray-800 mb-3">
												{f.label}
										</label>
											<div className="relative">
												<input 
													className="w-full px-5 py-4 border-2 border-gray-200 rounded-xl focus:ring-4 focus:ring-indigo-100 focus:border-indigo-400 transition-all duration-200 text-gray-900 placeholder-gray-400 group-hover:border-gray-300" 
													placeholder={f.placeholder || `Enter ${f.label.toLowerCase()}`}
													type={f.type || 'text'} 
													value={values[f.id] || ''} 
													onChange={e => setValues(v => ({...v, [f.id]: e.target.value}))} 
												/>
												{values[f.id] && (
													<div className="absolute right-3 top-1/2 transform -translate-y-1/2">
														<div className="w-5 h-5 bg-green-100 rounded-full flex items-center justify-center">
															<svg className="w-3 h-3 text-green-600" fill="currentColor" viewBox="0 0 20 20">
																<path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
															</svg>
														</div>
													</div>
												)}
											</div>
										</div>
									))}
								</div>
							</div>
						))}

						<div className="flex items-center justify-between mt-12 pt-8 border-t border-gray-100">
							<button 
								className="inline-flex items-center px-6 py-3 border-2 border-gray-300 rounded-xl text-gray-700 hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 font-semibold"
								onClick={() => setFormStep(1)}
							>
								<svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
								</svg>
								Back
							</button>
							<div className="flex items-center space-x-6">
								<div className="text-right">
									<p className="text-sm font-medium text-gray-700">Step 1 of 5</p>
									<p className="text-xs text-gray-500">Foundation setup in progress</p>
								</div>
								<button 
									className="group inline-flex items-center px-10 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 shadow-lg shadow-indigo-200/50 hover:shadow-xl hover:shadow-indigo-300/50"
									onClick={() => setCurrentStep('data-intake')}
								>
									Continue to Data Intake
									<svg className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
									</svg>
								</button>
							</div>
						</div>
					</div>
				</div>
			)}
		</div>
	)

	const renderDataIntakeStep = () => (
		<div className="max-w-7xl mx-auto">
			<div className="space-y-8">
				{groups.slice(1).map((g, groupIndex) => {
					const descriptions = [
						"Business structure, ownership details, and governance framework",
						"Federal tax registration, EIN requirements, and IRS compliance",
						"Optional early-stage requirements and additional considerations",
						"Document management, evidence storage, and filing organization"
					];

					const completedFields = g.fields.filter(f => values[f.id]?.trim()).length;
					const progressPercent = (completedFields / g.fields.length) * 100;

					return (
						<div key={g.title} className="bg-white rounded-3xl border border-gray-100 shadow-xl shadow-gray-100/50 overflow-hidden">
							<div className="bg-gradient-to-r from-indigo-50 via-white to-purple-50 p-8 border-b border-gray-100">
								<div className="flex items-center justify-between">
									<div>
										<h3 className="text-2xl font-bold text-gray-900 mb-1">{g.title}</h3>
										<p className="text-gray-600">{descriptions[groupIndex]}</p>
									</div>
									<div className="text-right">
										<div className="flex items-center space-x-3 mb-2">
											<span className="text-sm font-semibold text-gray-700">
												{completedFields}/{g.fields.length} completed
											</span>
											<div className="w-3 h-3 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full"></div>
										</div>
										<div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
											<div 
												className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 transition-all duration-500 ease-out"
												style={{ width: `${progressPercent}%` }}
											/>
										</div>
									</div>
								</div>
							</div>
							
							<div className="p-10">
								<div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
									{g.fields.map(f => (
										<div key={f.id} className="group">
											<label className="block text-sm font-semibold text-gray-800 mb-3">
												{f.label}
											</label>
											<div className="relative">
												<input 
													className="w-full px-5 py-4 border-2 border-gray-200 rounded-xl focus:ring-4 focus:ring-indigo-100 focus:border-indigo-400 transition-all duration-200 text-gray-900 placeholder-gray-400 group-hover:border-gray-300" 
													placeholder={f.placeholder || `Enter ${f.label.toLowerCase()}`}
													type={f.type || 'text'} 
													value={values[f.id] || ''} 
													onChange={e => setValues(v => ({...v, [f.id]: e.target.value}))} 
												/>
												{values[f.id]?.trim() && (
													<div className="absolute right-3 top-1/2 transform -translate-y-1/2">
														<div className="w-5 h-5 bg-green-100 rounded-full flex items-center justify-center">
															<svg className="w-3 h-3 text-green-600" fill="currentColor" viewBox="0 0 20 20">
																<path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
															</svg>
						</div>
					</div>
				)}
											</div>
										</div>
									))}
								</div>
							</div>
						</div>
					);
				})}
			</div>

			<div className="flex items-center justify-between mt-12 pt-8">
				<button 
					className="inline-flex items-center px-8 py-4 border-2 border-gray-300 rounded-xl text-gray-700 hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 font-semibold"
					onClick={() => setCurrentStep('setup')}
				>
					<svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
					</svg>
					Back to Setup
				</button>
				<div className="flex items-center space-x-6">
					<div className="text-right">
						<p className="text-sm font-semibold text-gray-700">Step 2 of 5</p>
						<p className="text-xs text-gray-500">Comprehensive data collection</p>
					</div>
					<button 
						className="group inline-flex items-center px-10 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 shadow-lg shadow-indigo-200/50 hover:shadow-xl hover:shadow-indigo-300/50"
						onClick={() => setCurrentStep('handoff')}
					>
						Continue to Handoff
						<svg className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
						</svg>
					</button>
				</div>
			</div>
		</div>
	)

	const renderHandoffStep = () => (
		<div className="max-w-2xl mx-auto py-12">
			<div className="bg-white rounded-xl border border-gray-200 p-8">
				<div className="text-center mb-8">
					<div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
						<svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
						</svg>
					</div>
					<h2 className="text-xl font-semibold text-gray-900 mb-2">Ready for Legal Review</h2>
					<p className="text-gray-600">Your information has been collected and is being prepared for filing</p>
				</div>

				<div className="space-y-4 mb-8">
					<div className="flex items-center justify-between py-3 px-4 bg-green-50 rounded-lg border border-green-200">
						<div className="flex items-center space-x-3">
							<div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center">
								<svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
									<path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
								</svg>
							</div>
							<span className="font-medium text-green-900">Information Complete</span>
						</div>
						<span className="text-green-700 text-sm">✓ Done</span>
					</div>

					<div className="flex items-center justify-between py-3 px-4 bg-blue-50 rounded-lg border border-blue-200">
						<div className="flex items-center space-x-3">
							<div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
								<div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
							</div>
							<span className="font-medium text-blue-900">Connect to Rocket Lawyer</span>
						</div>
						<span className="text-blue-700 text-sm">In Progress</span>
					</div>

					<div className="flex items-center justify-between py-3 px-4 bg-gray-50 rounded-lg border border-gray-200">
						<div className="flex items-center space-x-3">
							<div className="w-5 h-5 bg-gray-300 rounded-full flex items-center justify-center">
								<div className="w-2 h-2 bg-white rounded-full"></div>
							</div>
							<span className="font-medium text-gray-700">State Filing</span>
						</div>
						<span className="text-gray-500 text-sm">Pending Payment</span>
					</div>
				</div>

				<div className="border-t border-gray-200 pt-6 mb-8">
					<h3 className="font-semibold text-gray-900 mb-3">Legal Partnership</h3>
					<p className="text-gray-600 text-sm leading-relaxed">
						Rocket Lawyer will handle your business formation documents and serve as your registered agent, 
						ensuring proper filing with the Secretary of State and ongoing compliance.
					</p>
				</div>

				<button 
					className="w-full bg-blue-600 text-white font-medium py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors"
					onClick={() => setCurrentStep('payment')}
				>
					Continue to Payment
				</button>
			</div>
		</div>
	)

	const renderPaymentStep = () => (
		<div className="max-w-4xl mx-auto py-8">
			<div className="bg-white rounded-xl border border-gray-200 p-8">
				<div className="text-center mb-8">
					<h2 className="text-2xl font-semibold text-gray-900 mb-2">Complete Your Payment</h2>
					<p className="text-gray-600">Secure payment to finalize your business formation</p>
				</div>

				<div className="grid lg:grid-cols-2 gap-8">
					{/* Fee Summary */}
					<div className="space-y-4">
						<h3 className="font-semibold text-gray-900 mb-4">Fee Summary</h3>
						
						<div className="flex justify-between py-3 border-b border-gray-100">
							<div>
								<div className="font-medium text-gray-900">State Filing Fee</div>
								<div className="text-sm text-gray-500">Official government registration</div>
							</div>
							<div className="font-semibold text-gray-900">$125</div>
						</div>

						<div className="flex justify-between py-3 border-b border-gray-100">
							<div>
								<div className="font-medium text-gray-900">Professional Service Fee</div>
								<div className="text-sm text-gray-500">Rocket Lawyer legal services</div>
							</div>
							<div className="font-semibold text-gray-900">$99</div>
						</div>

						<div className="flex justify-between items-center py-3 border-b border-gray-100">
							<div className="flex items-center">
								<input 
									type="checkbox" 
									id="expedited"
									checked={paymentData.expedited}
									onChange={e => setPaymentData(prev => ({...prev, expedited: e.target.checked}))}
									className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
								/>
								<div className="ml-3">
									<label htmlFor="expedited" className="font-medium text-gray-900 cursor-pointer">Expedited Processing</label>
									<div className="text-sm text-gray-500">Priority handling and faster turnaround</div>
								</div>
							</div>
							<div className="font-semibold text-gray-900">+ $50</div>
						</div>

						<div className="flex justify-between items-center pt-4">
							<div className="text-lg font-semibold text-gray-900">Total</div>
							<div className="text-2xl font-bold text-gray-900">
								${224 + (paymentData.expedited ? 50 : 0)}
							</div>
						</div>
					</div>

					{/* Payment Methods */}
					<div className="space-y-6">
						<h3 className="font-semibold text-gray-900 mb-4">Payment Method</h3>
						
						{/* Apple Pay */}
						<button className="w-full bg-black text-white py-3 px-4 rounded-lg hover:bg-gray-800 transition-colors flex items-center justify-center space-x-2">
							<svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
								<path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/>
							</svg>
							<span className="font-medium">Pay with Apple Pay</span>
						</button>

						<div className="relative">
							<div className="absolute inset-0 flex items-center">
								<div className="w-full border-t border-gray-200"></div>
							</div>
							<div className="relative flex justify-center text-sm">
								<span className="px-2 bg-white text-gray-500">or pay with card</span>
							</div>
						</div>

						{/* Card Form */}
						<div className="space-y-4">
							<div>
								<label className="block text-sm font-medium text-gray-700 mb-2">Card Number</label>
								<input 
									type="text" 
									placeholder="1234 5678 9012 3456"
									value={paymentData.cardNumber}
									onChange={e => setPaymentData(prev => ({...prev, cardNumber: e.target.value}))}
									className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
								/>
							</div>

							<div className="grid grid-cols-2 gap-4">
								<div>
									<label className="block text-sm font-medium text-gray-700 mb-2">Expiry Date</label>
									<input 
										type="text" 
										placeholder="MM/YY"
										value={paymentData.expiry}
										onChange={e => setPaymentData(prev => ({...prev, expiry: e.target.value}))}
										className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
									/>
								</div>
								<div>
									<label className="block text-sm font-medium text-gray-700 mb-2">Security Code</label>
									<input 
										type="text" 
										placeholder="CVC"
										value={paymentData.cvc}
										onChange={e => setPaymentData(prev => ({...prev, cvc: e.target.value}))}
										className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
									/>
								</div>
							</div>
						</div>
					</div>
				</div>

				<div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-200">
					<button 
						className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
						onClick={() => setCurrentStep('handoff')}
					>
						Back
					</button>
					<button 
						className="px-8 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
						onClick={() => setCurrentStep('dashboard')}
					>
						Complete Payment
					</button>
				</div>

				<div className="mt-4 text-center">
					<p className="text-xs text-gray-500">
						🔒 Secure payment processing with 256-bit SSL encryption
					</p>
				</div>
			</div>
		</div>
	)

	const renderDashboardStep = () => (
		<div className="max-w-6xl mx-auto py-8">
			<div className="bg-white rounded-xl border border-gray-200 p-8">
				<div className="text-center mb-8">
					<h2 className="text-2xl font-semibold text-gray-900 mb-2">Business Formation Complete</h2>
					<p className="text-gray-600">Your business has been successfully registered and filed</p>
				</div>

				{/* Status Overview */}
				<div className="grid md:grid-cols-3 gap-6 mb-8">
					<div className="text-center p-4 bg-white rounded-lg border border-gray-200">
						<div className="text-2xl font-bold text-gray-900 mb-1">✓ Filed</div>
						<div className="text-sm text-gray-600">Business registration complete</div>
					</div>
					<div className="text-center p-4 bg-white rounded-lg border border-gray-200">
						<div className="text-2xl font-bold text-gray-900 mb-1">2 Pending</div>
						<div className="text-sm text-gray-600">Actions required</div>
					</div>
					<div className="text-center p-4 bg-white rounded-lg border border-gray-200">
						<div className="text-2xl font-bold text-gray-900 mb-1">5 Documents</div>
						<div className="text-sm text-gray-600">Ready for access</div>
					</div>
				</div>

				<div className="grid lg:grid-cols-2 gap-8 mb-8">
					{/* Outstanding Actions */}
					<div className="space-y-4">
						<h3 className="font-semibold text-gray-900 mb-4">Outstanding Actions</h3>
						
						<div className="flex justify-between items-center py-3 px-4 bg-white rounded-lg border border-gray-200">
							<div>
								<div className="font-medium text-gray-900">Upload EIN Letter</div>
								<div className="text-sm text-gray-600">Required once issued by IRS</div>
							</div>
							<button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm">
								Complete
							</button>
						</div>

						<div className="flex justify-between items-center py-3 px-4 bg-white rounded-lg border border-gray-200">
							<div>
								<div className="font-medium text-gray-900">Upload State Certificate</div>
								<div className="text-sm text-gray-600">Official formation document</div>
							</div>
							<button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm">
								Complete
							</button>
						</div>
					</div>

					{/* Available Documents */}
					<div className="space-y-4">
						<h3 className="font-semibold text-gray-900 mb-4">Available Documents</h3>
						
						<div className="flex justify-between items-center py-3 px-4 bg-white rounded-lg border border-gray-200">
							<div>
								<div className="font-medium text-gray-900">Articles of Organization</div>
								<div className="text-sm text-gray-600">Filed with state</div>
							</div>
							<button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm">
								Download
							</button>
						</div>

						<div className="flex justify-between items-center py-3 px-4 bg-white rounded-lg border border-gray-200">
							<div>
								<div className="font-medium text-gray-900">Filing Receipt</div>
								<div className="text-sm text-gray-600">Payment confirmation</div>
							</div>
							<button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm">
								Download
							</button>
						</div>

						<div className="flex justify-between items-center py-3 px-4 bg-white rounded-lg border border-gray-200">
							<div>
								<div className="font-medium text-gray-900">Operating Agreement</div>
								<div className="text-sm text-gray-600">Template ready for customization</div>
							</div>
							<button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm">
								View
							</button>
						</div>

						<div className="flex justify-between items-center py-3 px-4 bg-white rounded-lg border border-gray-200">
							<div>
								<div className="font-medium text-gray-900">Business License Application</div>
								<div className="text-sm text-gray-600">Ready for submission</div>
							</div>
							<button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm">
								Download
							</button>
						</div>

						<div className="flex justify-between items-center py-3 px-4 bg-white rounded-lg border border-gray-200">
							<div>
								<div className="font-medium text-gray-900">Tax ID Documentation</div>
								<div className="text-sm text-gray-600">EIN application materials</div>
							</div>
							<button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm">
								Download
							</button>
						</div>
					</div>
				</div>

				<div className="text-center mt-8">
					<button 
						className="px-8 py-3 bg-gray-600 text-white font-medium rounded-lg hover:bg-gray-700 transition-colors"
						onClick={handleDashboardClose}
					>
						Close Dashboard
					</button>
				</div>
			</div>


		</div>
	)

	const renderCurrentStep = () => {
		switch (currentStep) {
			case 'setup': return renderSetupStep()
			case 'data-intake': return renderDataIntakeStep()
			case 'handoff': return renderHandoffStep()
			case 'payment': return renderPaymentStep()
			case 'dashboard': return renderDashboardStep()
			default: return renderSetupStep()
		}
	}

	if (inline) {
		return (
			<div className="rounded-2xl border border-gray-200 bg-white shadow-sm p-6">
				<ProgressBar />
				{renderCurrentStep()}
			</div>
		)
	}

	return (
		<div className="fixed inset-0 z-40">
			<div className="absolute inset-0 bg-black/30" onClick={onClose} />
			<div className="absolute inset-2 md:inset-4 lg:inset-6 rounded-3xl bg-gray-50 shadow-2xl border border-gray-200 overflow-hidden">
				<div className="h-full flex flex-col">
					<div className="p-6 md:p-8 border-b border-gray-200 bg-white">
						<div className="flex items-center justify-between mb-6">
							<div className="text-xl font-bold text-gray-900">Business Setup Workflow</div>
							<button 
								className="w-10 h-10 rounded-full border border-gray-300 hover:bg-gray-50 flex items-center justify-center transition-colors" 
								onClick={onClose} 
								aria-label="Close"
							>
								✕
							</button>
						</div>
						<ProgressBar />
								</div>
					<div className="flex-1 overflow-auto p-6 md:p-8">
						{renderCurrentStep()}
								</div>
							</div>
										</div>

			{/* Legal Assistant Chat - Available throughout workflow */}
			{showAssistantChat && (
				<div className="fixed bottom-4 right-4 w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-50">
					<div className="p-4 border-b border-gray-200 flex items-center justify-between">
						<h3 className="font-semibold text-gray-900">Legal Assistant</h3>
						<button 
							onClick={() => setShowAssistantChat(false)}
							className="text-gray-400 hover:text-gray-600"
							aria-label="Close Legal Assistant"
						>
							<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
									</div>
					
					<div className="h-64 overflow-y-auto p-4 space-y-3">
						{assistantMessages.map((msg, i) => (
							<div key={i} className={`flex ${msg.from === 'user' ? 'justify-end' : 'justify-start'}`}>
								<div className={`max-w-xs px-3 py-2 rounded-lg text-sm ${
									msg.from === 'user' 
										? 'bg-blue-600 text-white' 
										: 'bg-gray-100 text-gray-900'
								}`}>
									{msg.text}
								</div>
							</div>
						))}
					</div>
					
					<div className="p-4 border-t border-gray-200">
						<div className="flex space-x-2">
							<input
								type="text"
								value={assistantInput}
								onChange={(e) => setAssistantInput(e.target.value)}
								placeholder="Ask about legal requirements..."
								className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
								onKeyDown={(e) => e.key === 'Enter' && sendAssistantMessage()}
							/>
							<button
								onClick={sendAssistantMessage}
								className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
							>
								Send
							</button>
						</div>
					</div>
				</div>
			)}

			{/* Legal Assistant Floating Button - Available throughout workflow */}
			{!showAssistantChat && (
				<button
					onClick={() => setShowAssistantChat(true)}
					className="fixed bottom-4 right-4 w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 transition-colors flex items-center justify-center z-40"
					aria-label="Open Legal Assistant"
				>
					<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
					</svg>
				</button>
			)}



		</div>
	)
} 