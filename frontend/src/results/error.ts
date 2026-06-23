import { escapeHtml } from './utils';

export function render_query_error(err: any) {
  const resultsErrorMessage = document.getElementById('resultErrorMessage')! as HTMLSpanElement;
  const resultsErrorQuery = document.getElementById('resultsErrorQuery')! as HTMLPreElement;
  if (err.data) {
    switch (err.data.type) {
      case 'QLeverException':
        resultsErrorMessage.textContent = err.data.exception;
        if (err.data.metadata) {
          resultsErrorQuery.innerHTML =
            escapeHtml(err.data.query.substring(0, err.data.metadata.startIndex)) +
            `<span class="text-red-500 dark:text-red-600 font-bold">${escapeHtml(err.data.query.substring(err.data.metadata.startIndex, err.data.metadata.stopIndex + 1))}</span>` +
            escapeHtml(err.data.query.substring(err.data.metadata.stopIndex + 1));
        } else {
          resultsErrorQuery.innerHTML = err.data.query;
        }
        break;
      case 'Connection':
        resultsErrorMessage.innerHTML = `The connection to the SPARQL endpoint is broken (${err.data.statusText}).<br> The most common cause is that the QLever server is down. Please try again later and contact us if the error perists`;
        resultsErrorQuery.innerText = err.data.query;
        break;
      case 'Canceled':
        resultsErrorMessage.innerHTML = `Operation was manually cancelled.`;
        resultsErrorQuery.innerText = err.data.query;
        break;
      case 'InvalidFormat':
        resultsErrorMessage.innerHTML = `Update result could not be deserialized: ${err.data.message}`;
        resultsErrorQuery.innerText = err.data.query;
        break;
      case 'Deserialization':
        resultsErrorMessage.innerHTML = `Query result could not be deserialized: ${err.data.message}`;
        resultsErrorQuery.innerText = err.data.query;
        break;
      default:
        console.log('uncaught error:', err);
        resultsErrorMessage.innerHTML = `Something went wrong but we don't know what...`;
        break;
    }
  }
  const resultsContainer = document.getElementById('results') as HTMLSelectElement;
  resultsContainer.classList.add('hidden');
  const resultsError = document.getElementById('resultsError') as HTMLSelectElement;
  resultsError.classList.remove('hidden');
  window.scrollTo({
    top: resultsError.offsetTop + 10,
    behavior: 'smooth',
  });
  throw new Error('Query processing error');
}
